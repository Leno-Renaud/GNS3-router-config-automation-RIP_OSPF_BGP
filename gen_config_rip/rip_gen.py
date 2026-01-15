import json
import os
from pathlib import Path
from jinja2 import Template

def cfg_generation_rip():
    topo_path = Path("../get_topology/topology.json")
    if not topo_path.is_absolute():
        # Try to find it relative to current script if not found in CWD
        script_dir = Path(__file__).parent
        if not topo_path.exists() and (script_dir / topo_path).exists():
           topo_path = script_dir / topo_path

    with open(topo_path) as f:
        topo = json.load(f)

    routers_data = {r["name"]: r for r in topo["routers"] if r.get("protocol", "").upper() == "RIP"}
    
    # Load template from same dir as script
    template_path = Path(__file__).parent / "router_rip.j2"
    with open(template_path) as f:
        template = Template(f.read())
    configs_dict = {}

    for router_name in routers_data.keys():
        # Loopback Generation (derive from router name digits)
        router_num = ''.join(filter(str.isdigit, router_name))
        if not router_num:
             router_num = "1"
        loopback_ip = f"2000::{router_num}/128"

        config = template.render(
            name=router_name,
            interfaces=routers_data[router_name]["interfaces"],
            networks=routers_data[router_name]["networks"],
            loopback_ip=loopback_ip
        )
            
        configs_dict[router_name] = config
    
    return configs_dict

if __name__ == "__main__":
    try:
        print(cfg_generation_rip())
    except Exception as e:
        print(f"Error: {e}")