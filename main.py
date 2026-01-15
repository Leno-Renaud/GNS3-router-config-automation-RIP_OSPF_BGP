#!/usr/bin/env python3
"""
Orchestrateur Principal (GUI Version):
1. Sélection du projet GNS3 via Interface Graphique.
2. Configuration du préfixe IPv6 via Dialogue.
3. Exécution séquentielle de l'automatisation.
"""

import json
import os
import shutil
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
from pathlib import Path

# Imports des modules
from get_topology.get_topology import get_topology
from gen_config_bgp_rip.bgp_rip_gen import generate_bgp_configs as gen_rip
from gen_config_bgp_ospf.bgp_ospf_gen import generate_bgp_configs as gen_ospf
from injection_cfgs.inject_cfgs import injection_cfg


def run_automation(gns3_file_path, ip_prefix, loopback_format="simple"):
    """
    Exécute la logique d'automatisation avec les paramètres fournis.
    """
    gns3_file = Path(gns3_file_path)
    project_dir = gns3_file.parent
    
    # Dossiers de travail
    ROOT_DIR = Path(__file__).parent.absolute()
    OUTPUT_CONFIGS_DIR = ROOT_DIR / "configs"
    TOPOLOGY_JSON = ROOT_DIR / "topology.json"
    
    print("\n" + "="*60)
    print(f"      DEMARRAGE AUTOMATISATION")
    print(f"      Projet: {gns3_file.name}")
    print(f"      Préfixe IP: {ip_prefix}")
    print(f"      Format Loopback: {loopback_format}")
    print("="*60)

    # 1. EXTRACTION DE LA TOPOLOGIE
    print(f"\n[1/4] Extraction de la topologie...")
    topo_data = get_topology(
        gns3_file, 
        ip_base=ip_prefix, 
        output_dir=ROOT_DIR, 
        output_name="topology.json",
        loopback_format=loopback_format
    )
    
    if topo_data is None:
        if TOPOLOGY_JSON.exists():
            print("  ! Rechargement depuis topology.json existant...")
            with open(TOPOLOGY_JSON, 'r', encoding='utf-8') as f:
                topo_data = json.load(f)
        else:
            return False, "Impossible de charger la topologie."

    # 2. GENERATION DES CONFIGURATIONS
    print("\n[2/4] Génération des configurations...")
    if OUTPUT_CONFIGS_DIR.exists(): shutil.rmtree(OUTPUT_CONFIGS_DIR) 
    OUTPUT_CONFIGS_DIR.mkdir(exist_ok=True)

    print("  -> Génération RIP...")
    gen_rip(TOPOLOGY_JSON, output_dir=OUTPUT_CONFIGS_DIR)
    
    print("  -> Génération OSPF...")
    gen_ospf(TOPOLOGY_JSON, output_dir=OUTPUT_CONFIGS_DIR)
    
    # 3. VERIFICATION DU NOMBRE DE CONFIGURATIONS
    print("\n[3/4] Vérification du nombre de configurations...")
    count = len(list(OUTPUT_CONFIGS_DIR.glob("*.cfg")))
    if count != len(topo_data.get("routers", [])):
        print(f"  [AVERTISSEMENT] Nombre de configurations générées ({count}) ne correspond pas au nombre de routeurs dans la topologie ({len(topo_data.get('routers', []))}).")
    else:
        print(f"  Nombre de configurations générées : {count}")
    
    # 4. INJECTION DANS GNS3
    print("\n[4/4] Injection dans le projet GNS3...")
    injection_cfg(project_dir=str(project_dir), configs_dir=str(OUTPUT_CONFIGS_DIR))
    
    return True, f"Succès ! {count} configurations générées et injectées."


def show_tutorial(root):
    """
    Affiche une fenêtre d'aide expliquant comment préparer le projet GNS3.
    """
    tuto = tk.Toplevel(root)
    tuto.title("Guide de préparation GNS3")
    tuto.geometry("600x650") 
    
    tuto.grab_set()
    tuto.focus_force() 

    # Conteneur principal
    main_frame = ttk.Frame(tuto, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    ttk.Label(main_frame, text="Pré-requis : Structure GNS3", font=("Helvetica", 16, "bold")).pack(pady=(0, 15))

    # --- ETAPE 1 : CABLAGE ---
    step0 = ttk.LabelFrame(main_frame, text="1. Positionnement & Câblage", padding=5)
    step0.pack(fill=tk.X, pady=5)
    tk.Label(step0, justify=tk.LEFT, wraplength=550, text=(
        "Placez vos routeurs dans l'espace de travail et reliez-les entre eux (câblez les interfaces)."
    )).pack(anchor="w")

    # --- ETAPE 2 : LES RECTANGLES ---
    step1 = ttk.LabelFrame(main_frame, text="2. Définir les Protocoles et AS", padding=5)
    step1.pack(fill=tk.X, pady=5)
    
    tk.Label(step1, justify=tk.LEFT, wraplength=550, text=(
        "Utilisez l'outil 'Draw Rectangle' pour définir les zones.\n"
        "La couleur de BORDURE définit le protocole :"
    )).pack(anchor="w")
    
    f_colors = ttk.Frame(step1)
    f_colors.pack(fill=tk.X, pady=2)
    
    tk.Label(f_colors, text="  ●  ", fg="#FF0000", font=("Arial", 14)).pack(side=tk.LEFT)
    tk.Label(f_colors, text="ROUGE = RIP", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    
    tk.Label(f_colors, text="      ●  ", fg="#00FF00", font=("Arial", 14)).pack(side=tk.LEFT)
    tk.Label(f_colors, text="VERT = OSPF", font=("Arial", 10, "bold")).pack(side=tk.LEFT)

    # --- ETAPE 3 : ARRIERE PLAN ---
    step2 = ttk.LabelFrame(main_frame, text="3. IMPORTANT : Arrière-plan", padding=5)
    step2.pack(fill=tk.X, pady=5)
    
    tk.Label(step2, justify=tk.LEFT, wraplength=550, text=(
        "Clic-Droit sur chaque rectangle > 'Lower one layer'.\n"
        "Sinon, les routeurs seront cachés par le rectangle."
    )).pack(anchor="w")

    # --- ETAPE 4 : EXTINCTION ---
    step3 = ttk.LabelFrame(main_frame, text="4. CRITIQUE : Eteindre les routeurs", padding=5)
    step3.pack(fill=tk.X, pady=5)
    
    tk.Label(step3, justify=tk.LEFT, wraplength=550, fg="red", font=("Arial", 10, "bold"), text=(
        "Avant de continuer :\n"
        "Assurez-vous que TOUS les routeurs sont ETEINTS (Stop).\n"
        "L'injection de configuration ne fonctionne que si les routeurs sont à l'arrêt."
    )).pack(anchor="w")

    # --- BOUTON IMAGE (ASSETS) ---
    assets_dir = Path(__file__).parent / "assets"
    tuto_img_path = assets_dir / "tuto_gns3.png"
    
    def open_image():
        if tuto_img_path.exists():
            # Ouvre l'image avec le visualiseur par défaut du système 
            os.startfile(tuto_img_path)
        else:
            messagebox.showinfo("Image manquante", f"L'image d'aide n'a pas été trouvée dans :\n{assets_dir}")

    if tuto_img_path.exists():
        btn = ttk.Button(main_frame, text="📷 Voir l'exemple en Image (Ouvrir)", command=open_image)
        btn.pack(pady=15, ipady=5)
    else:
        ttk.Label(main_frame, text="(Image d'aide non trouvée)", fg="gray").pack(pady=10)

    # Bouton OK
    ttk.Button(main_frame, text="Tout est prêt -> Sélectionner le projet", command=tuto.destroy).pack(side=tk.BOTTOM, pady=10)
    
    # Attendre la fermeture
    root.wait_window(tuto)


def main_gui():
    root = tk.Tk()
    root.withdraw() # Cacher la fenêtre principale vide
    
    # 0. Afficher le tutoriel
    show_tutorial(root)

    # 1. Sélectionner le fichier GNS3
    print("En attente de sélection du fichier .gns3...")
    file_path = filedialog.askopenfilename(
        title="Sélectionnez votre fichier de projet GNS3 (.gns3)",
        filetypes=[("GNS3 Project", "*.gns3"), ("All Files", "*.*")]
    )

    if not file_path:
        print("Annulé par l'utilisateur.")
        return

    # 2. Demander le préfixe IP
    ip_base = simpledialog.askstring(
        "Configuration IPv6", 
        "Entrez le préfixe de base IPv6 pour le projet :\n(Format attendu : 2000:1::/64)\n\nNote: L'adressage des liens sera de la forme :\nIntra-AS: 2000:1:AS:ID1:ID2::ID/80\nInter-AS: 2000:1:0:AS1:AS2:ID1:ID2::ID/112",
        initialvalue="2000:1::/64"
    )

    if not ip_base:
        print("Annulé par l'utilisateur.")
        return
        
    # 2b. Demander le format de Loopback
    class LoopbackDialog(simpledialog.Dialog):
        def body(self, master):
            tk.Label(master, text="Choisissez le format des adresses Loopback :").pack(pady=5)
            self.var = tk.StringVar(value="simple")

            tk.Radiobutton(master, text="Avec AS (2000:2:AS::R1)", variable=self.var, value="with_as").pack(anchor='w')
            tk.Radiobutton(master, text="Simple (2000::R1)", variable=self.var, value="simple").pack(anchor='w')
            
            return None # initial focus

        def apply(self):
            self.result = self.var.get()

    # Création d'une fenêtre temporaire si root est caché
    loopback_choice = LoopbackDialog(root, title="Format Loopback").result
    if not loopback_choice: 
        loopback_choice = "simple" # Default

    # 3. Lancer le traitement
    success, message = run_automation(file_path, ip_base, loopback_choice)
    
    if success:
        messagebox.showinfo("Terminé", message)
    else:
        messagebox.showerror("Erreur", message)

if __name__ == "__main__":
    main_gui()
