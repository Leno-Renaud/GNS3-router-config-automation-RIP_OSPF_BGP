"""
Script principal pour générer automatiquement les configurations BGP des routeurs.
Workflow : GNS3 project -> topology_bgp.json -> fichiers .cfg BGP
"""

from pathlib import Path
from cfg_generation_bgp import cfg_generation_bgp
from get_topology_bgp import extract_topology_bgp


def main():
    """
    Fonction principale orchestrant l'extraction de topologie et la génération de configs BGP.
    
    Étapes :
    1. Extrait la topologie depuis le projet GNS3
    2. Génère topology_bgp.json avec l'adressage IP + ASN + voisins
    3. Crée les fichiers .cfg pour chaque routeur avec BGP configuré
    """
    # --- Configuration des paramètres ---
    base_dir = Path(__file__).parent.absolute()
    gns3_project_file = r"C:\Users\Hector\Desktop\INSA Lyon\3A-TC\S1\GNS Projet\blank_project\blank_project.gns3"
    ip_base = "2000:1::/64"
    asn_base = 65000
    topology_filename = "topology_bgp.json"
    
    # Extraire la topologie avec ASN et voisins
    extract_topology_bgp(gns3_project_file, ip_base, asn_base, base_dir, topology_filename)
    
    # Générer les configurations
    cfg_generation_bgp(topology_filename, base_dir)

if __name__ == "__main__":
    main()
