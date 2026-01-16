#!/usr/bin/env python3
"""
GNS3 Network Automation Tool
Version GUI Moderne (ttkbootstrap)
"""

import json
import shutil
from pathlib import Path
from tkinter import PhotoImage

import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox

# Modules métier (inchangés)
from get_topology.get_topology import get_topology
from gen_config_bgp_rip.bgp_rip_gen import generate_bgp_configs as gen_rip
from gen_config_bgp_ospf.bgp_ospf_gen import generate_bgp_configs as gen_ospf
from injection_cfgs.injection_cfgs import injection_cfg


# ===================== LOGIQUE METIER ===================== #

def run_automation(gns3_file_path, ip_prefix, loopback_format, options):
    ROOT = Path(__file__).parent
    CONFIG_DIR = ROOT / "configs"
    TOPO_JSON = ROOT / "topology.json"

    topo = get_topology(
        gns3_file_path,
        ip_base=ip_prefix,
        output_dir=ROOT,
        output_name="topology.json",
        loopback_format=loopback_format
    )

    if topo is None and TOPO_JSON.exists():
        topo = json.load(open(TOPO_JSON))

    if topo is None:
        return False, "Impossible de charger la topologie."

    if CONFIG_DIR.exists():
        shutil.rmtree(CONFIG_DIR)
    CONFIG_DIR.mkdir()

    gen_rip(TOPO_JSON, CONFIG_DIR, options)
    gen_ospf(TOPO_JSON, CONFIG_DIR, options)

    count = len(list(CONFIG_DIR.glob("*.cfg")))
    injection_cfg(
        project_dir=str(Path(gns3_file_path).parent),
        configs_dir=str(CONFIG_DIR)
    )

    return True, f"{count} configurations générées et injectées."


# ===================== UI ===================== #

class App(tb.Window):
    def __init__(self):
        super().__init__(
            title="GNS3 Network Automation",
            themename="darkly",
            size=(920, 720),
            resizable=(False, False)
        )
        self.project_file = None
        self.options = {}

        # Définir l'icône dans la barre des tâches
        try:
            icon_path = str(Path(__file__).parent / "assets/cameleon.png")
            self.icon = PhotoImage(file=icon_path)
            self.iconphoto(False, self.icon)
        except:
            pass

        self.build_ui()

    def build_ui(self):
        container = tb.Frame(self, padding=30)
        container.pack(fill=BOTH, expand=True)

        tb.Label(
            container,
            text="GNS3 Network Automation",
            font=("Segoe UI", 22, "bold")
        ).pack(anchor=W, pady=(0, 25))

        notebook = tb.Notebook(container)
        notebook.pack(fill=BOTH, expand=True)

        self.tab_project = tb.Frame(notebook, padding=20)
        self.tab_address = tb.Frame(notebook, padding=20)
        self.tab_advanced = tb.Frame(notebook, padding=20)

        notebook.add(self.tab_project, text="Projet")
        notebook.add(self.tab_address, text="Adressage")
        notebook.add(self.tab_advanced, text="Options avancées")

        self.build_project_tab()
        self.build_address_tab()
        self.build_advanced_tab()

        tb.Separator(container).pack(fill=X, pady=15)

        tb.Button(
            container,
            text="Lancer l'automatisation",
            bootstyle=SUCCESS,
            width=30,
            command=self.launch
        ).pack()

    # ---------- ONGLET PROJET ---------- #

    def build_project_tab(self):
        card = tb.Labelframe(self.tab_project, text="Projet GNS3", padding=20)
        card.pack(fill=X)

        self.lbl_project = tb.Label(card, text="Aucun projet sélectionné")
        self.lbl_project.pack(anchor=W, pady=5)

        tb.Button(
            card,
            text="Sélectionner un fichier .gns3",
            bootstyle=PRIMARY,
            command=self.select_project
        ).pack(anchor=W, pady=10)

    def select_project(self):
        file = filedialog.askopenfilename(
            title="Sélectionnez un projet GNS3",
            filetypes=[("GNS3 Project", "*.gns3")]
        )
        if file:
            self.project_file = file
            self.lbl_project.config(text=file)

    # ---------- ONGLET ADRESSAGE ---------- #

    def build_address_tab(self):
        card = tb.Labelframe(self.tab_address, text="IPv6", padding=20)
        card.pack(fill=X)

        tb.Label(card, text="Préfixe réseau").pack(anchor=W)
        self.entry_prefix = tb.Entry(card, width=40)
        self.entry_prefix.insert(0, "2000:1::/64")
        self.entry_prefix.pack(anchor=W, pady=5)

        tb.Label(card, text="Format Loopback").pack(anchor=W, pady=(15, 5))
        self.loopback = tb.StringVar(value="with_as")

        tb.Radiobutton(card, text="Avec AS", variable=self.loopback, value="with_as").pack(anchor=W)
        tb.Radiobutton(card, text="Simple", variable=self.loopback, value="simple").pack(anchor=W)

    # ---------- ONGLET OPTIONS AVANCEES ---------- #

    def build_advanced_tab(self):
        card = tb.Labelframe(self.tab_advanced, text="Fonctionnalités", padding=20)
        card.pack(fill=X)

        self.secure_redist = tb.BooleanVar(value=True)
        self.policies = tb.BooleanVar(value=False)
        self.metrics = tb.BooleanVar(value=False)

        tb.Checkbutton(
            card,
            text="Redistribution sécurisée (Route-Maps)",
            variable=self.secure_redist
        ).pack(anchor=W, pady=5)

        tb.Checkbutton(
            card,
            text="Politiques BGP (Gao-Rexford)",
            variable=self.policies
        ).pack(anchor=W, pady=5)

        tb.Checkbutton(
            card,
            text="Optimisation métriques OSPF",
            variable=self.metrics
        ).pack(anchor=W, pady=5)

    # ---------- EXECUTION ---------- #

    def launch(self):
        if not self.project_file:
            messagebox.showerror("Erreur", "Veuillez sélectionner un projet GNS3.")
            return

        self.options = {
            "secure_redist": self.secure_redist.get(),
            "policies_enabled": self.policies.get(),
            "ospf_costs": {},
            "bgp_relations": {}
        }

        ok, msg = run_automation(
            self.project_file,
            self.entry_prefix.get(),
            self.loopback.get(),
            self.options
        )

        if ok:
            messagebox.showinfo("Succès", msg)
        else:
            messagebox.showerror("Erreur", msg)


# ===================== MAIN ===================== #

if __name__ == "__main__":
    App().mainloop()