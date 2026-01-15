#!/usr/bin/env python3
"""
IPv6 BGP+RIP Config Generator (Unified iBGP/eBGP with RIP as IGP)
"""
import json
import os
import sys
from pathlib import Path
from jinja2 import Template
import sys

# Add root directory to sys.path to allow importing utils
sys.path.append(str(Path(__file__).parent.parent))
from utils import get_router_id, get_loopback_ip

def generate_bgp_configs(topology_file, output_dir="configs"):
    print(f"Loading topology from {topology_file}...")
    with open(topology_file, 'r') as f:
        topo = json.load(f)

    # Prepare data structures
    routers = {r["name"]: r for r in topo["routers"]}
    links = topo.get("links", [])
    loopback_fmt = topo.get("loopback_format", "simple")
    
    # Enrich router data with deduced fields
    for name, r in routers.items():
        r["router_id"] = get_router_id(name)
        r["loopback_ip"] = get_loopback_ip(name, fmt=loopback_fmt, as_number=r.get("as_number"))
        # Default ASN if missing (fallback for safety)
        if "as_number" not in r or r["as_number"] is None:
            r["as_number"] = 65000 
        r["bgp_neighbors"] = []
        # Initialize RIP enabled on all interfaces by default (will be disabled for eBGP links)
        for iface in r.get("interfaces", []):
            iface["rip_enabled"] = True

    # Infer neighbors
    # 1. Process Links for eBGP (Direct Physical Peering) and RIP disabling
    for link in links:
        a_name = link["a"]
        b_name = link["b"]
        
        if a_name not in routers or b_name not in routers:
            continue

        rA = routers[a_name]
        rB = routers[b_name]
        
        asA = rA["as_number"]
        asB = rB["as_number"]
        
        # Get interface IPs for the link
        def get_ip(router_data, iface_name):
            for i in router_data["interfaces"]:
                if i["name"] == iface_name:
                    return i["ip"]
            return None

        ipA = get_ip(rA, link["a_iface"])
        ipB = get_ip(rB, link["b_iface"])

        if not ipA or not ipB:
            print(f"Warning: Could not find IP for link {a_name}<->{b_name}")
            continue

        # eBGP Logic: Different AS -> Peer physically
        if asA != asB:
            # Setup side A if it is RIP
            if rA.get("protocol") == "RIP":
                rA["bgp_neighbors"].append({
                    "name": b_name,
                    "ip": ipB,
                    "asn": asB,
                    "is_ibgp": False
                })
                # Disable RIP on this interface (eBGP link)
                for iface in rA["interfaces"]:
                    if iface["name"] == link["a_iface"]:
                        iface["rip_enabled"] = False
            
            # Setup side B if it is RIP
            if rB.get("protocol") == "RIP":
                rB["bgp_neighbors"].append({
                    "name": a_name,
                    "ip": ipA,
                    "asn": asA,
                    "is_ibgp": False
                })
                # Disable RIP on this interface (eBGP link)
                for iface in rB["interfaces"]:
                    if iface["name"] == link["b_iface"]:
                        iface["rip_enabled"] = False

    # 2. Process Full Mesh for iBGP (Loopback Peering) within same AS for RIP routers
    rip_router_names = [n for n, r in routers.items() if r.get("protocol") == "RIP"]

    for i in range(len(rip_router_names)):
        for j in range(i + 1, len(rip_router_names)):
            nameA = rip_router_names[i]
            nameB = rip_router_names[j]
            
            rA = routers[nameA]
            rB = routers[nameB]
            
            if rA["as_number"] == rB["as_number"]:
                # iBGP Peering A -> B
                rA["bgp_neighbors"].append({
                    "name": nameB,
                    "ip": rB["loopback_ip"],
                    "asn": rB["as_number"],
                    "is_ibgp": True
                })
                # iBGP Peering B -> A
                rB["bgp_neighbors"].append({
                    "name": nameA,
                    "ip": rA["loopback_ip"],
                    "asn": rA["as_number"],
                    "is_ibgp": True
                })

    # Generate Configs
    out_path = Path(output_dir)
    os.makedirs(out_path, exist_ok=True)
    
    # Use templates from local directory
    template_path = Path(__file__).parent / "router_bgp_rip.j2"
        
    with open(template_path) as f:
        template = Template(f.read())
        
    print(f"Generating BGP+RIP configs in {out_path}...")
    
    for name in rip_router_names:
        r = routers[name]
        
        # Remove duplicates in neighbors
        unique_neighbors = {n["ip"]: n for n in r["bgp_neighbors"]}.values()
        
        # Determine if router is a Border Router (has eBGP neighbors)
        is_border = any(not n["is_ibgp"] for n in unique_neighbors)
        
        config = template.render(
            router_name=name,
            router_id=r["router_id"],
            loopback_ip=r["loopback_ip"],
            asn=r["as_number"],
            interfaces=r["interfaces"],
            neighbors=unique_neighbors,
            networks=r.get("networks", []),
            is_border=is_border
        )
        
        with open(out_path / f"{name}.cfg", "w") as f:
            f.write(config)
        print(f"  Saved {name}.cfg ({'iBGP' if any(n['is_ibgp'] for n in unique_neighbors) else ''} {'eBGP' if is_border else ''})")

if __name__ == "__main__":
    topo_file = Path(__file__).parent / "topology.json"
    if not topo_file.exists():
        print("Error: topology.json not found in local directory.")
        sys.exit(1)
        
    generate_bgp_configs(topo_file)
