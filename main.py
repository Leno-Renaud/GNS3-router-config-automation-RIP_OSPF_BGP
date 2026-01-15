#!/usr/bin/env python3
"""
Orchestrateur Principal:
1. Extrait la topologie du fichier GNS3.
2. Identifie les protocoles par AS.
3. Génère les configurations (BGP+RIP ou BGP+OSPF).
4. Injecte les configurations dans le projet GNS3.
"""

import json
import os
import shutil
from pathlib import Path

# Imports des modules
from get_topology.get_topology import extract_topology
from hector_is_brewing.bgp_rip_gen import generate_bgp_configs as gen_rip
from hector_is_brewing.bgp_ospf_gen import generate_bgp_configs as gen_ospf
from InjectionCFG.inject_cfgs import injection_cfg


def main():
    # --- CONFIGURATION ---
    # Chemin vers votre projet GNS3 (dossier contenant le .gns3)
    # Adaptez ce chemin à votre environnement réel
    GNS3_PROJECT_DIR = r"C:\Users\Hector\Desktop\INSA Lyon\3A-TC\S1\GNS Projet\architecture_finale"
    
    # Trouver le fichier .gns3 automatiquement
    try:
        gns3_file = list(Path(GNS3_PROJECT_DIR).glob("*.gns3"))[0]
    except IndexError:
        print(f"Erreur: Aucun fichier .gns3 trouvé dans {GNS3_PROJECT_DIR}")
        return

    # Dossiers de travail
    ROOT_DIR = Path(__file__).parent.absolute()
    OUTPUT_CONFIGS_DIR = ROOT_DIR / "configs"
    # Le fichier topology.json sera généré à la racine par extract_topology car output_dir=ROOT_DIR
    TOPOLOGY_JSON = ROOT_DIR / "topology.json"
    
    # Paramètres réseau
    IP_BASE = "2000:1::/64"

    print("="*60)
    print("      GNS3 NETWORK AUTOMATION ORCHESTRATOR")
    print("="*60)

    # 1. EXTRACTION DE LA TOPOLOGIE
    print(f"\n[1/4] Extraction de la topologie depuis {gns3_file.name}...")
    topo_data = extract_topology(gns3_file, ip_base=IP_BASE, output_dir=ROOT_DIR, output_name="topology.json")
    
    # Fail-safe: si la fonction ne retourne rien (cas étrange observé), on recharge le fichier JSON
    if topo_data is None:
        print("  ! extract_topology a retourné None, tentatives de rechargement depuis topology.json...")
        if TOPOLOGY_JSON.exists():
            with open(TOPOLOGY_JSON, 'r', encoding='utf-8') as f:
                topo_data = json.load(f)
        else:
            print("Erreur CRITIQUE : Impossible de charger la topologie.")
            return

    # 2. GENERATION DES CONFIGURATIONS
    print("\n[2/4] Génération des configurations...")
    
    # Nettoyage et création du dossier de sortie
    if OUTPUT_CONFIGS_DIR.exists(): shutil.rmtree(OUTPUT_CONFIGS_DIR) 
    OUTPUT_CONFIGS_DIR.mkdir(exist_ok=True)

    print("  -> Génération RIP (pour routeurs RIP)...")
    # Le générateur RIP a été modifié pour ne traiter QUE les routeurs marqués "RIP"
    # Il écrit directement dans le dossier final configs/
    gen_rip(TOPOLOGY_JSON, output_dir=OUTPUT_CONFIGS_DIR)
    
    print("  -> Génération OSPF (pour routeurs OSPF)...")
    # Le générateur OSPF a été modifié pour ne traiter QUE les routeurs marqués "OSPF"
    # Il écrit directement dans le dossier final configs/ (n'écrase pas RIP car routeurs différents)
    gen_ospf(TOPOLOGY_JSON, output_dir=OUTPUT_CONFIGS_DIR)
    
    # 3. VERIFICATION
    # Cette étape remplace la "Fusion" car la fusion est maintenant implicite
    print("\n[3/4] Vérification de la complétude...")
    count = len(list(OUTPUT_CONFIGS_DIR.glob("*.cfg")))
    
    for router in topo_data["routers"]:
        name = router["name"]
        proto = router["protocol"]
        cfg_path = OUTPUT_CONFIGS_DIR / f"{name}.cfg"
        
        if cfg_path.exists():
            print(f"  [OK] {name} : Config {proto} générée.")
        else:
            if proto == "UNKNOWN":
                print(f"  [SKIP] {name} : Pas de protocole détecté (hors des rectangles AS ?).")
            else:
                print(f"  [ERREUR] {name} : Config {proto} manquante !")

    print(f"  -> Total : {count} fichiers de configuration prêts.")

    # 4. INJECTION DANS GNS3
    print("\n[4/4] Injection dans le projet GNS3...")
    # On passe les chemins sous forme de str pour éviter les soucis de compatibilité
    injection_cfg(project_dir=str(GNS3_PROJECT_DIR), configs_dir=str(OUTPUT_CONFIGS_DIR))
    
    print("\n" + "="*60)
    print("SUCCESS: Automation Complete!")
    print("="*60)
    print("Vous pouvez recharger les routeurs dans GNS3.")

if __name__ == "__main__":
    main()
