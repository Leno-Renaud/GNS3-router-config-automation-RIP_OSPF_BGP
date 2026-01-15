#!/usr/bin/env python3
"""
IPv6 BGP+RIP Config Generator (Unified iBGP/eBGP with RIP as IGP)
"""
import json
import os
import sys
from pathlib import Path
from jinja2 import Template

def get_loopback_ip(router_name):
    # Extract router number for Loopback IP: 2000::{N}
    router_num = ''.join(filter(str.isdigit, router_name))
    if not router_num:
        router_num = "1"
    return f"2000::{router_num}"

def get_router_id(router_name):
    # Extract router number for Router ID: N.N.N.N
    router_num = ''.join(filter(str.isdigit, router_name))
    if not router_num:
        router_num = "1"
    return f"{router_num}.{router_num}.{router_num}.{router_num}"

def generate_bgp_configs(topology_file, output_dir="configs"):
    print(f"Loading topology from {topology_file}...")
    with open(topology_file, 'r') as f:
        topo = json.load(f)

    # Prepare data structures
    routers = {r["name"]: r for r in topo["routers"]}
    links = topo.get("links", [])
    
    # Enrich router data with deduced fields
    for name, r in routers.items():
        r["router_id"] = get_router_id(name)
        r["loopback_ip"] = get_loopback_ip(name)
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
            # A -> B
            rA["bgp_neighbors"].append({
                "name": b_name,
                "ip": ipB,
                "asn": asB,
                "is_ibgp": False
            })
            # B -> A
            rB["bgp_neighbors"].append({
                "name": a_name,
                "ip": ipA,
                "asn": asA,
                "is_ibgp": False
            })
            
            # Disable RIP on these interfaces (eBGP link)
            for iface in rA["interfaces"]:
                if iface["name"] == link["a_iface"]:
                    iface["rip_enabled"] = False
            for iface in rB["interfaces"]:
                if iface["name"] == link["b_iface"]:
                    iface["rip_enabled"] = False

    # 2. Process Full Mesh for iBGP (Loopback Peering) within same AS
    router_names = list(routers.keys())
    for i in range(len(router_names)):
        for j in range(i + 1, len(router_names)):
            nameA = router_names[i]
            nameB = router_names[j]
            
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
    out_path = Path(__file__).parent / output_dir
    os.makedirs(out_path, exist_ok=True)
    
    template_path = Path(__file__).parent / "router_bgp_rip.j2"
    with open(template_path) as f:
        template = Template(f.read())
        
    print(f"Generating BGP+RIP configs in {out_path}...")
    
    for name, r in routers.items():
        # Remove duplicates in neighbors
        unique_neighbors = {n["ip"]: n for n in r["bgp_neighbors"]}.values()
        
        config = template.render(
            router_name=name,
            router_id=r["router_id"],
            loopback_ip=r["loopback_ip"],
            asn=r["as_number"],
            interfaces=r["interfaces"],
            neighbors=unique_neighbors,
            networks=r.get("networks", [])
        )
        
        with open(out_path / f"{name}.cfg", "w") as f:
            f.write(config)
        print(f"  Saved {name}.cfg ({'iBGP' if any(n['is_ibgp'] for n in unique_neighbors) else ''} {'eBGP' if any(not n['is_ibgp'] for n in unique_neighbors) else ''})")

if __name__ == "__main__":
    topo_file = Path(__file__).parent / "topology.json"
    if not topo_file.exists():
        print("Error: topology.json not found in hector_is_brewing/")
        sys.exit(1)
        
    generate_bgp_configs(topo_file)
