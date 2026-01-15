from InjectionCFG.inject_cfgs import extract_topology
from codes_rip.cfg_generation_rip import cfg_generation_rip

def main():
    gns3_project = r"C:\Users\Hector\Desktop\INSA Lyon\3A-TC\S1\GNS Projet\blank_project\blank_project.gns3"
    ip_base = "2000:1::/64"
    
    print("=" * 60)
    print("Test d'extraction de topologie")
    print("=" * 60)
    extract_topology(gns3_project, ip_base)

    ripDict = cfg_generation_rip()
    print(ripDict)