#!/usr/bin/env python3
"""
IPv6 BGP Config Generator (Unified iBGP/eBGP)
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
        # Initialize OSPF enabled on all interfaces by default (will be disabled for eBGP links)
        for iface in r.get("interfaces", []):
            iface["ospf_enabled"] = True

    # Infer neighbors from links
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
        # We need to find which interface connects to the other router
        # But topo["links"] already says which interface is used.
        # We must look up that interface's IP in the router's interface list.
        
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

        # DECISION LOGIC: iBGP vs eBGP
        
        # LINK: A -> B
        if asA == asB:
            # iBGP: Peer with Loopback IP
            neighbor_config = {
                "name": b_name,
                "ip": rB["loopback_ip"], # Peer with Loopback
                "asn": asB,
                "is_ibgp": True
            }
        else:
            # eBGP: Peer with physical interface IP
            neighbor_config = {
                "name": b_name,
                "ip": ipB, # Peer with directly connected IP
                "asn": asB,
                "is_ibgp": False
            }
            # Disable OSPF on this interface for both routers
            for iface in rA["interfaces"]:
                if iface["name"] == link["a_iface"]:
                    iface["ospf_enabled"] = False
            for iface in rB["interfaces"]:
                if iface["name"] == link["b_iface"]:
                    iface["ospf_enabled"] = False
            
        rA["bgp_neighbors"].append(neighbor_config)

        # LINK: B -> A
        if asA == asB:
            # iBGP
            neighbor_config = {
                "name": a_name,
                "ip": rA["loopback_ip"],
                "asn": asA,
                "is_ibgp": True
            }
        else:
            # eBGP
            neighbor_config = {
                "name": a_name,
                "ip": ipA,
                "asn": asA,
                "is_ibgp": False
            }
        rB["bgp_neighbors"].append(neighbor_config)

    # Generate Configs
    out_path = Path(__file__).parent / output_dir
    os.makedirs(out_path, exist_ok=True)
    
    template_path = Path(__file__).parent / "router_bgp_ospf.j2"
    with open(template_path) as f:
        template = Template(f.read())
        
    print(f"Generating BGP+OSPF configs in {out_path}...")
    
    for name, r in routers.items():
        # Remove duplicates in neighbors (in case of multiple links)
        # Using dictionary comprehension to unique-ify by IP
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
