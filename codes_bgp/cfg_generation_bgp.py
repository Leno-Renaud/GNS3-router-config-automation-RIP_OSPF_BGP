import json
from jinja2 import Template
import re

def generate_router_id(router_name):
    """
    Génère un router-id IPv4 à partir du nom du routeur
    Ex: R1 -> 1.1.1.1
    """
    match = re.search(r"\d+", router_name)
    if match:
        n = int(match.group())
        return f"{n}.{n}.{n}.{n}"
    else:
        return "1.1.1.1"


def cfg_generation_bgp(topology, output_dir="."):
    with open(topology) as f:
        topo = json.load(f)
    
    routers_data = {r["name"]: r for r in topo["routers"]}
    
    template = Template(open("router_bgp.j2").read())
    
    for router_name, router in routers_data.items():
        router_id = generate_router_id(router_name)

        config = template.render(
            name=router_name,
            asn=router["asn"],
            router_id=router_id,
            interfaces=router["interfaces"],
            neighbors=router["neighbors"]
        )
        
        output_file = f"{output_dir}/{router_name}.cfg"
        with open(output_file, "w") as f:
            f.write(config)
        
        print(f"[BGP] Config générée : {output_file}")
    
    print("[BGP] Configurations BGP générées avec succès.")


cfg_generation_bgp("topology_bgp.json")