#!/usr/bin/env python3
"""
IPv6 OSPFv3 Config Generator for GNS3 c7200 routers
Accepts topology.json from get_topology.py (shared format with RIP/BGP)
Generates .cfg files with OSPFv3 configuration
"""

import json
import os
import sys
from jinja2 import Template


def load_topology(json_file):
    """Load the topology JSON file (format from get_topology.py)."""
    with open(json_file, 'r') as f:
        return json.load(f)


def create_ospfv3_config(router_name, router_data):
    """
    Create OSPFv3 configuration for a single router.
    Expects router_data with 'interfaces' list (ip, prefix, name).
    Returns the config as a string.
    """
    # Extract router number for Router ID
    router_num = ''.join(filter(str.isdigit, router_name))
    if not router_num:
        router_num = "1"

    router_id = f"{router_num}.{router_num}.{router_num}.{router_num}"
    loopback_ip = f"2000::{router_num}/128"

    interfaces = router_data.get("interfaces", [])
    all_iface_names = [iface["name"] for iface in interfaces]
    default_ifaces = ["GigabitEthernet1/0", "GigabitEthernet2/0", "GigabitEthernet3/0"]

    # Load template and render to produce identical output
    template_path = os.path.join(os.path.dirname(__file__), "router_ospf.j2")
    with open(template_path, 'r', encoding='utf-8') as tf:
        template = Template(tf.read())

    rendered = template.render(
        router_name=router_name,
        interfaces=interfaces,
        iface_names=all_iface_names,
        default_ifaces=default_ifaces,
        router_id=router_id,
        loopback_ip=loopback_ip,
    )

    # Ensure trailing newline behavior matches previous implementation
    return rendered.rstrip() + "\n"


def generate_all_configs(topology, output_dir="configs"):
    """Generate configuration files for all routers."""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating OSPFv3 configurations from topology...")
    print("-" * 60)
    
    routers = topology.get("routers", [])
    
    for router_data in routers:
        router_name = router_data["name"]
        print(f"Creating config for {router_name}...")
        
        # Generate the config
        config = create_ospfv3_config(router_name, router_data)
        
        # Save to .cfg file
        filename = f"{router_name}.cfg"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w") as f:
            f.write(config)
        
        print(f"  Saved to: {filepath}")
        
        # Display a summary of what's configured
        interfaces = router_data.get("interfaces", [])
        if interfaces:
            print(f"  Interfaces configured:")
            for iface in interfaces:
                print(f"    {iface['name']}: {iface['ip']}/{iface['prefix']}")
        else:
            print(f"  No interfaces configured (all shutdown)")
    
    print("\n" + "=" * 60)
    print(f"Done! OSPFv3 configurations saved in '{output_dir}/' directory")
    print("\nIMPORTANT FOR OSPFv3:")
    print("1. All interfaces are pre-configured with 'no shutdown'")
    print("2. Loopback0 is configured with /128 as passive interface")
    print("3. OSPFv3 is enabled on all active interfaces (area 0)")
    print("\nTo use in GNS3:")
    print("1. Stop the routers in GNS3")
    print("2. Replace their startup-config.cfg files with these .cfg files")
    print("3. Start the routers")
    print("=" * 60)


def main():
    """Main function - handles command line arguments."""
    if len(sys.argv) > 1:
        # Load topology from provided file
        json_file = sys.argv[1]
        print(f"Loading topology from {json_file}...")
        topology = load_topology(json_file)
    else:
        # Default: try topology.json next to this script, then fallback to cwd
        script_dir = os.path.dirname(os.path.abspath(__file__))
        script_topo = os.path.join(script_dir, "topology.json")
        cwd_topo = os.path.join(os.getcwd(), "topology.json")

        if os.path.exists(script_topo):
            print(f"Loading topology from {script_topo}...")
            topology = load_topology(script_topo)
        elif os.path.exists(cwd_topo):
            print(f"Loading topology from {cwd_topo}...")
            topology = load_topology(cwd_topo)
        else:
            print(f"Error: topology.json not found. Please provide topology file as argument.")
            sys.exit(1)
    
    # Generate configurations
    generate_all_configs(topology)


if __name__ == "__main__":
    main()
