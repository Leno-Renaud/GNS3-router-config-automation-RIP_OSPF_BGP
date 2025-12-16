#!/usr/bin/env python3
"""
IPv6 OSPFv3 Config Generator for GNS3 c7200 routers
Takes a simple JSON topology and generates .cfg files with OSPFv3 configuration
"""

import json
import ipaddress
import os
import sys

def load_topology(json_file):
    """Load the topology JSON file."""
    with open(json_file, 'r') as f:
        return json.load(f)

def generate_ipv6_addresses(topology):
    """
    Generate IPv6 addresses for all links based on ipv6_base.
    Returns a dict mapping (router, interface) -> (ipv6, prefix_length)
    """
    # Parse the base IPv6 network
    ipv6_base = topology.get("ipv6_base", "2001:db8::/64")
    base_network = ipaddress.ip_network(ipv6_base, strict=False)
    
    # Get all links
    links = topology.get("links", [])
    
    # We'll assign IPv6 addresses from sequential /64 subnets
    ipv6_assignments = {}
    
    # Generate /64 subnets from the base network
    subnet_gen = base_network.subnets(new_prefix=64)
    
    # Process each link
    for i, link in enumerate(links):
        try:
            # Get the next /64 subnet
            subnet = next(subnet_gen)
            
            # Assign ::1 address to router A
            ipv6_a = str(subnet.network_address + 1)  # e.g., 2001:db8::1
            # Assign ::2 address to router B  
            ipv6_b = str(subnet.network_address + 2)  # e.g., 2001:db8::2
            
            prefix_length = subnet.prefixlen  # Should be 64
            
            # Store assignments
            ipv6_assignments[(link["a"], link["a_iface"])] = (ipv6_a, prefix_length)
            ipv6_assignments[(link["b"], link["b_iface"])] = (ipv6_b, prefix_length)
            
        except StopIteration:
            print(f"Error: Ran out of IPv6 addresses at link {i}")
            break
    
    return ipv6_assignments

def create_ospfv3_config(router_name, router_data, ipv6_assignments, topology):
    """
    Create OSPFv3 configuration for a single router.
    Returns the config as a string.
    """
    config_lines = []
    
    # 1. Basic hostname
    config_lines.append(f"hostname {router_name}")
    config_lines.append("!")
    
    # 2. Enable IPv6 unicast routing (required for OSPFv3)
    config_lines.append("ipv6 unicast-routing")
    config_lines.append("!")
    
    # 3. Configure interfaces with IPv6 addresses
    config_lines.append("! Interface configurations")
    for interface in router_data["interfaces"]:
        interface_name = interface["name"]
        config_lines.append(f"interface {interface_name}")
        
        # Check if this interface has an IPv6 assignment
        key = (router_name, interface_name)
        if key in ipv6_assignments:
            ipv6, prefix_length = ipv6_assignments[key]
            config_lines.append(f" ipv6 address {ipv6}/{prefix_length}")
            config_lines.append(" ipv6 enable")
            config_lines.append(" no shutdown")
        else:
            config_lines.append(" shutdown")
        
        config_lines.append("!")
    
    # 4. OSPFv3 configuration
    config_lines.append("! OSPFv3 configuration")
    config_lines.append("ipv6 router ospf 1")
    
    # Generate router ID from last octet (R1 -> 1.1.1.1, R2 -> 2.2.2.2, etc.)
    # Note: OSPFv3 still uses 32-bit router IDs (IPv4 format)
    router_num = ''.join(filter(str.isdigit, router_name))
    if router_num:
        router_id = f"{router_num}.{router_num}.{router_num}.{router_num}"
    else:
        router_id = "1.1.1.1"
    
    config_lines.append(f" router-id {router_id}")
    config_lines.append("!")
    
    # 5. Enable OSPFv3 on interfaces
    config_lines.append("! Enable OSPFv3 on interfaces")
    for interface in router_data["interfaces"]:
        interface_name = interface["name"]
        key = (router_name, interface_name)
        
        if key in ipv6_assignments:
            config_lines.append(f"interface {interface_name}")
            config_lines.append(" ipv6 ospf 1 area 0")
            config_lines.append("!")
    
    # 6. End with save command
    config_lines.append("end")
    config_lines.append("write memory")
    
    return "\n".join(config_lines)

def generate_all_configs(topology, output_dir="configs"):
    """Generate configuration files for all routers."""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate IPv6 addresses for all links
    print("Generating IPv6 addresses for links...")
    ipv6_assignments = generate_ipv6_addresses(topology)
    
    # Print IPv6 assignments for verification
    print("\nIPv6 Address Assignments:")
    print("-" * 50)
    for (router, iface), (ipv6, prefix) in ipv6_assignments.items():
        print(f"{router}:{iface} -> {ipv6}/{prefix}")
    
    # Generate config for each router
    print("\nGenerating router configurations...")
    print("-" * 50)
    
    for router_data in topology["routers"]:
        router_name = router_data["name"]
        print(f"Creating config for {router_name}...")
        
        # Generate the config
        config = create_ospfv3_config(router_name, router_data, ipv6_assignments, topology)
        
        # Save to .cfg file
        filename = f"{router_name}.cfg"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "w") as f:
            f.write(config)
        
        print(f"  Saved to: {filepath}")
        
        # Display a summary of what's configured
        print(f"  OSPFv3 interfaces enabled:")
        for interface in router_data["interfaces"]:
            key = (router_name, interface["name"])
            if key in ipv6_assignments:
                ipv6, prefix = ipv6_assignments[key]
                print(f"    {interface['name']}: {ipv6}/{prefix}")
    
    print("\n" + "=" * 60)
    print(f"Done! Configurations saved in '{output_dir}/' directory")
    print("\nIMPORTANT FOR OSPFv3:")
    print("1. OSPFv3 requires 'ipv6 unicast-routing' to be enabled")
    print("2. Router ID must be set (still IPv4 format)")
    print("3. OSPFv3 is enabled per interface with 'ipv6 ospf 1 area 0'")
    print("\nTo use in GNS3:")
    print("1. Stop the routers in GNS3")
    print("2. Replace their startup-config.cfg files with these .cfg files")
    print("3. Start the routers")
    print("=" * 60)

def create_sample_json():
    """Create a sample topology JSON file with IPv6."""
    sample = {
        "routers": [
            {
                "name": "R1",
                "interfaces": [
                    {"name": "GigabitEthernet1/0"}
                ]
            },
            {
                "name": "R2",
                "interfaces": [
                    {"name": "GigabitEthernet1/0"},
                    {"name": "GigabitEthernet2/0"}
                ]
            },
            {
                "name": "R3",
                "interfaces": [
                    {"name": "GigabitEthernet2/0"}
                ]
            }
        ],
        "links": [
            {"a": "R1", "a_iface": "GigabitEthernet1/0", "b": "R2", "b_iface": "GigabitEthernet1/0"},
            {"a": "R2", "a_iface": "GigabitEthernet2/0", "b": "R3", "b_iface": "GigabitEthernet2/0"}
        ],
        "ipv6_base": "2001:db8::/64"
    }
    
    with open("topology_ipv6.json", "w") as f:
        json.dump(sample, f, indent=2)
    
    print("Created sample topology_ipv6.json")
    return sample

def main():
    """Main function - handles command line arguments."""
    
    if len(sys.argv) > 1:
        # Load topology from provided file
        json_file = sys.argv[1]
        print(f"Loading topology from {json_file}...")
        topology = load_topology(json_file)
    else:
        # Create and use sample topology
        print("No input file provided. Creating sample IPv6 topology...")
        topology = create_sample_json()
        print("\nUsing sample topology_ipv6.json")
    
    # Generate configurations
    generate_all_configs(topology)

if __name__ == "__main__":
    main()
