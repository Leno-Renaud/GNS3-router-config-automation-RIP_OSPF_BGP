"""
Script principal pour générer automatiquement les configurations RIP des routeurs.
Workflow complet : GNS3 project -> topology.json -> fichiers .cfg
"""

from pathlib import Path
from cfg_generation import cfg_generation
from get_topology import extract_topology


def main():
    """
    Fonction principale orchestrant l'extraction de topologie et la génération de configs.
    
    Étapes :
    1. Extrait la topologie depuis le projet GNS3
    2. Génère topology.json avec l'adressage IP calculé
    3. Crée les fichiers .cfg pour chaque routeur avec RIP configuré
    """
    # --- Configuration des paramètres ---
    # Répertoire de travail : où se trouve ce script
    base_dir = Path(__file__).parent.absolute()
    gns3_project_file = r"C:\Users\Hector\Desktop\INSA Lyon\3A-TC\S1\GNS Projet\blank_project\blank_project.gns3"
    ip_base = "2000:1::/64"
    topology_filename = "topology.json"
    extract_topology(gns3_project_file, ip_base, base_dir, topology_filename)
    cfg_generation(topology_filename, ip_base)

if __name__ == "__main__":
    main()
