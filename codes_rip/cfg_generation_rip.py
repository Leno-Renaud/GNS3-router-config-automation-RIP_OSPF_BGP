import json
from jinja2 import Template

def cfg_generation(topology, ip_base):
    with open(topology) as f:
        topo = json.load(f)

    routers_data = {r["name"]: r for r in topo["routers"]}
    
    template = Template(open("router_rip.j2").read())
    
    configs_dict = {}
    
    for router_name in routers_data.keys():
        config = template.render(
            name=router_name,
            interfaces=routers_data[router_name]["interfaces"],
            networks=routers_data[router_name]["networks"]
        )
        configs_dict[router_name] = config
    
    return configs_dict

# Exemple d'utilisation
configs = cfg_generation("topology.json", "2000:1::/64")
print(configs)