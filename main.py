from get_topology.get_topology import extract_topology
import json
from pathlib import Path
from codes_rip.cfg_generation_rip import cfg_generation_rip
from codes_ospf.ospfv3_gen import ospfv3_gen

def main():
    gns3_project = r"C:\Users\Hector\Desktop\INSA Lyon\3A-TC\S1\GNS Projet\blank_project\blank_project.gns3"
    ip_base = "2000:1::/64"
    
    print("=" * 60)
    print("Test d'extraction de topologie")
    print("=" * 60)
    #extract_topology(gns3_project, ip_base)

    # Charger la liste des routeurs depuis topology.json
    topo_path = Path("get_topology/topology.json")
    with open(topo_path) as f:
        topo = json.load(f)
    
    router_list = [r["name"] for r in topo["routers"]]
    
    # Générer les configs RIP et OSPF
    ripDict = cfg_generation_rip()
    ospfDict = ospfv3_gen()
    
    print("RIPDict", ripDict)
    print("OSPF", ospfDict)
    

    configs_output_dir = Path("configs")
    configs_output_dir.mkdir(exist_ok=True)
    
    for router_name in router_list:
        config_parts = []
        
        if router_name in ripDict:
            config_parts.append(ripDict[router_name])
        
        if router_name in ospfDict:
            config_parts.append(ospfDict[router_name])
        
        if config_parts:
            final_config = "\n".join(config_parts)
            cfg_file = configs_output_dir / f"{router_name}.cfg"
            with open(cfg_file, 'w') as f:
                f.write(final_config)
            print(f"Created {cfg_file}")

main()