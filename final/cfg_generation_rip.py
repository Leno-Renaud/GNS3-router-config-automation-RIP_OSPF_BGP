import json
from jinja2 import Template

def cfg_generation(topology, ip_base):
    with open(topology) as f:
        topo = json.load(f)

    routers_data = {r["name"]: r for r in topo["routers"]}
    
    template = Template(open("router_rip.j2").read())
    
    for router_name in routers_data.keys():
        config = template.render(
            name=router_name,
            interfaces=routers_data[router_name]["interfaces"],
            rip_networks=routers_data[router_name]["rip_networks"]
        )
        with open(f"{router_name}.cfg", "w") as f:
            f.write(config)
    
    print("Configurations RIPng générées avec succès.")
