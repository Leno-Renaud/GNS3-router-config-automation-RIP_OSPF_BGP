"""
IPv6 OSPFv3 Config Generator for GNS3 c7200 routers
Accepts topology.json from get_topology.py (shared format with RIP/BGP)
Generates configurations as dictionary (format matching cfg_generation_rip)
"""

import json
import os
import sys
from pathlib import Path
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
    template_path = Path(__file__).parent / "router_ospf.j2"
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


def ospfv3_gen():
    """Generate OSPFv3 configurations for all routers with protocol 'ospfv3'."""
    topo_path = Path("../get_topology/topology.json")
    if not topo_path.is_absolute():
        # Try to find it relative to current script if not found in CWD
        script_dir = Path(__file__).parent
        if not topo_path.exists() and (script_dir / topo_path).exists():
            topo_path = script_dir / topo_path

    with open(topo_path) as f:
        topo = json.load(f)

    routers_data = {r["name"]: r for r in topo["routers"] if r.get("protocol") == "OSPF"}
    
    configs_dict = {}

    for router_name in routers_data.keys():
        config = create_ospfv3_config(router_name, routers_data[router_name])
        configs_dict[router_name] = config
    
    return configs_dict


if __name__ == "__main__":
    try:
        print(ospfv3_gen() )
    except Exception as e:
        print(f"Error: {e}")