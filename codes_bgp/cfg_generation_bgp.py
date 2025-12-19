import json
from jinja2 import Template

def cfg_generation_bgp(topology, output_dir="."):
    """
    Génère les configurations BGP à partir du fichier topology_bgp.json
    
    Args:
        topology (str): Chemin vers le fichier topology_bgp.json
        output_dir (str): Répertoire où écrire les fichiers .cfg
    """
    with open(topology) as f:
        topo = json.load(f)

    routers_data = {r["name"]: r for r in topo["routers"]}
    
    template = Template(open("router_bgp.j2").read())
    
    for router_name in routers_data.keys():
        router = routers_data[router_name]
        config = template.render(
            name=router_name,
            asn=router["asn"],
            interfaces=router["interfaces"],
            neighbors=router["neighbors"]
        )
        
        output_file = f"{output_dir}/{router_name}.cfg"
        with open(output_file, "w") as f:
            f.write(config)
        print(f"[BGP] Config générée : {output_file}")
    
    print("[BGP] Configurations BGP générées avec succès.")
