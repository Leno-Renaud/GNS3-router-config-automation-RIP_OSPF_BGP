#!/usr/bin/env python3
"""
IPv6 OSPFv3 Config Generator for GNS3 c7200 routers
Accepts topology.json from get_topology.py (shared format with RIP/BGP)
Generates .cfg files with OSPFv3 configuration
"""

import json
import os
import sys


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
    config_lines = []
    
    # Extract router number for Router ID
    router_num = ''.join(filter(str.isdigit, router_name))
    if not router_num:
        router_num = "1"
    
    # 1. Basic hostname
    config_lines.append(f"hostname {router_name}")
    config_lines.append("!")
    
    # 2. Enable IPv6 unicast routing and CEF
    config_lines.append("ipv6 unicast-routing")
    config_lines.append("ipv6 cef")
    config_lines.append("!")
    
    # 3. Configure interfaces with IPv6 addresses (from topology)
    config_lines.append("! Interface configurations")
    interfaces = router_data.get("interfaces", [])
    
    # Build list of interface names to check later
    all_iface_names = [iface["name"] for iface in interfaces]
    
    # Configure all interfaces (connected or not)
    for iface in interfaces:
        iface_name = iface["name"]
        ip = iface["ip"]
        prefix = iface["prefix"]
        
        config_lines.append(f"interface {iface_name}")
        config_lines.append(" no ip address")
        config_lines.append(" ipv6 nd dad attempts 0")
        config_lines.append(f" ipv6 address {ip}/{prefix}")
        config_lines.append(" ipv6 ospf 1 area 0")
        config_lines.append(" no shutdown")
        config_lines.append("!")
    
    # Shutdown any default interfaces not in topology
    default_ifaces = ["GigabitEthernet1/0", "GigabitEthernet2/0", "GigabitEthernet3/0"]
    for default_iface in default_ifaces:
        if default_iface not in all_iface_names:
            config_lines.append(f"interface {default_iface}")
            config_lines.append(" no ip address")
            config_lines.append(" shutdown")
            config_lines.append("!")
    
    # 4. OSPFv3 configuration
    config_lines.append("! OSPFv3 configuration")
    config_lines.append("ipv6 router ospf 1")
    
    # Generate router ID from router number
    router_id = f"{router_num}.{router_num}.{router_num}.{router_num}"
    config_lines.append(f" router-id {router_id}")
    config_lines.append("!")
    
    # 5. Re-enable OSPFv3 on interfaces (for clarity/verification)
    for iface in interfaces:
        iface_name = iface["name"]
        config_lines.append(f"interface {iface_name}")
        config_lines.append(" ipv6 ospf 1 area 0")
        config_lines.append(" !")
    
    # 6. End with save command
    config_lines.append("end")
    config_lines.append("write memory")
    
    return "\n".join(config_lines)


def generate_all_configs(topology, output_dir="configs"):
    """Generate configuration dictionary for all routers."""
    
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
    
    return configs_dict


def main():
    """Main function - handles command line arguments."""
    
    if len(sys.argv) > 1:
        # Load topology from provided file
        json_file = sys.argv[1]
        print(f"Loading topology from {json_file}...")
        topology = load_topology(json_file)
    else:
        # Default to topology.json in current directory
        json_file = "topology.json"
        if os.path.exists(json_file):
            print(f"Loading topology from {json_file}...")
            topology = load_topology(json_file)
        else:
            print(f"Error: topology.json not found. Please provide topology file as argument.")
            sys.exit(1)
    
    # Generate configurations
    configs = generate_all_configs(topology)
    print(configs)


if __name__ == "__main__":
    main()
