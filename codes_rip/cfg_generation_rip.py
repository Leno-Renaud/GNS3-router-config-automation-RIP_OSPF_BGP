import json
import os
from pathlib import Path
from jinja2 import Template

def cfg_generation(topology_file, ip_base, output_dir="configs"):
    # Ensure topology_file is a Path or str
    topo_path = Path(topology_file)
    if not topo_path.is_absolute():
        # Try to find it relative to current script if not found in CWD
        script_dir = Path(__file__).parent
        if not topo_path.exists() and (script_dir / topo_path).exists():
           topo_path = script_dir / topo_path

    with open(topo_path) as f:
        topo = json.load(f)

    routers_data = {r["name"]: r for r in topo["routers"]}
    
    # Load template from same dir as script
    template_path = Path(__file__).parent / "router_rip.j2"
    with open(template_path) as f:
        template = Template(f.read())
    
    # Prepare output directory
    out_path = Path(__file__).parent / output_dir
    os.makedirs(out_path, exist_ok=True)
    
    configs_dict = {}
    print(f"Generating RIP configurations to {out_path}...")

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
        
        # Save to file
        with open(out_path / f"{router_name}.cfg", "w") as f:
            f.write(config)
            
        configs_dict[router_name] = config
        print(f"  Generated {router_name}.cfg")
    
    return configs_dict

if __name__ == "__main__":
    # Example usage
    topo = "topology.json"
    try:
        cfg_generation(topo, "2000:1::/64")
    except Exception as e:
        print(f"Error: {e}")