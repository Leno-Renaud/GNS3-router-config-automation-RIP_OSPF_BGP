import json
import os
import shutil
import glob

def injection_cfg(project_dir=None, configs_dir=None):
    PROJECT_DIR = project_dir

    GNS3_FILE = os.path.join(PROJECT_DIR, "blank_project.gns3") 
    # Try to find the .gns3 file dynamically if specific name not guaranteed
    gns3_files = glob.glob(os.path.join(PROJECT_DIR, "*.gns3"))
    if gns3_files:
        GNS3_FILE = gns3_files[0]

    DYNAMIPS_DIR = os.path.join(PROJECT_DIR, "project-files", "dynamips")

    CFG_DIR = configs_dir

    # Charger le projet GNS3
    with open(GNS3_FILE, "r", encoding="utf-8") as f:
        project = json.load(f)

    # Extraction des UUID par rapport au nom des noeuds (routeurs, switchs)
    nodes = project.get("topology", {}).get("nodes", [])
    name_to_id = {
        n["name"]: n["node_id"]
        for n in nodes
        if n.get("node_type") == "dynamips"
    }

    print("[INFO] Nodes dynamips détectés:", name_to_id)

    # Insertion du fichier .cfg dans la config de chaque routeur

    #ATTENTION : Nom exacte dans le cfg et dans gns
    for router, node_id in name_to_id.items():
        src = os.path.join(CFG_DIR, f"{router}.cfg")
        node_dir = os.path.join(DYNAMIPS_DIR, node_id, "configs")

        if not os.path.exists(src):
            print(f"[SKIP] {router}: fichier source absent ({src})")
            continue

        if not os.path.isdir(node_dir):
            print(f"[ERREUR] {router}: dossier configs introuvable ({node_dir})")
            continue

        # GNS3 utilise iX_startup-config.cfg
        candidates = glob.glob(os.path.join(node_dir, "i*_startup-config.cfg"))
        if not candidates:
            print(f"[ERREUR] {router}: aucun i*_startup-config.cfg trouvé dans {node_dir}")
            continue

        # Un seul fichier cfg attendu
        dst = candidates[0]
        
        shutil.copy(src, dst)
        print(f"[OK] {router}: {os.path.basename(src)} -> {os.path.relpath(dst, PROJECT_DIR)}")

    print("[DONE] Injection exacte (fichier réellement utilisé par GNS3).")

if __name__ == "__main__":
    injection_cfg()