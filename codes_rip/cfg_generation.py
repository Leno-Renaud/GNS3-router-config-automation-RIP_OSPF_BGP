import json
import ipaddress
from jinja2 import Template

def cfg_generation(topology):
    # --- ÉTAPE 1 : Charger le fichier de topologie JSON ---
    # Ouvre le fichier topology.json et le charge en dictionnaire Python
    with open(topology) as f:
        topo = json.load(f)

    # --- Crée un dictionnaire des routeurs indexé par nom ---
    routers_data = {r["name"]: r for r in topo["routers"]}
    print(f"ROUTEUR DATA {routers_data}\n")
    # --- Récupère la liste de tous les liens (connexions entre routeurs) ---
    links = topo["links"]
    print(f"LIEN {links}\n")
    # --- Crée l'objet réseau de base pour l'allocation d'adresses IP ---
    base_net = ipaddress.ip_network(topo["ip_base"])

    # --- Structures internes pour stocker la configuration ---
    # Dictionnaire qui associe chaque routeur à sa liste d'interfaces
    interfaces_cfg = {}
    # Dictionnaire qui associe chaque routeur à l'ensemble de ses réseaux RIP
    rip_networks = {}

    # Variable qui va parcourir les sous-réseaux : commence avec le réseau de base
    current_net = base_net

    # --- Boucle : pour chaque lien, on génère les IPs et les configurations ---
    for link in links:
        # Récupère le routeur source (a) et le nom de son interface
        a, a_iface_name = link["a"], link["a_iface"]
        # Récupère le routeur destination (b) et le nom de son interface
        b, b_iface_name = link["b"], link["b_iface"]

        # Si le routeur a n'existe pas dans interfaces_cfg, crée une liste vide
        if a not in interfaces_cfg:
            interfaces_cfg[a] = []
        # Si le routeur b n'existe pas dans interfaces_cfg, crée une liste vide
        if b not in interfaces_cfg:
            interfaces_cfg[b] = []
        # Si le routeur a n'existe pas dans rip_networks, crée un ensemble vide
        if a not in rip_networks:
            rip_networks[a] = set()
        # Si le routeur b n'existe pas dans rip_networks, crée un ensemble vide
        if b not in rip_networks:
            rip_networks[b] = set()

        # Récupère toutes les adresses IP utilisables du sous-réseau courant (exclut adresse réseau et broadcast)
        hosts = list(current_net.hosts())
        # Prend la première adresse pour le routeur a
        ip_a = hosts[0]
        # Prend la deuxième adresse pour le routeur b
        ip_b = hosts[1]

        # Ajoute l'interface du routeur a avec son nom, son IP et son masque
        interfaces_cfg[a].append({
            "name": a_iface_name,
            "ip": str(ip_a),
            "mask": str(current_net.netmask)
        })
        # Ajoute l'interface du routeur b avec son nom, son IP et son masque
        interfaces_cfg[b].append({
            "name": b_iface_name,
            "ip": str(ip_b),
            "mask": str(current_net.netmask)
        })
        # Ajoute le réseau du lien à l'ensemble des réseaux RIP du routeur a
        rip_networks[a].add(str(current_net.network_address))
        # Ajoute le réseau du lien à l'ensemble des réseaux RIP du routeur b
        rip_networks[b].add(str(current_net.network_address))
        # Calcule le prochain sous-réseau en avançant de la taille du réseau courant
        current_net = ipaddress.ip_network(
            int(current_net.network_address) + current_net.num_addresses
        ).supernet(new_prefix=current_net.prefixlen)

    # --- Charge le contenu du fichier de template Jinja2 et le prépare pour remplissage ---
    template = Template(open("router_rip.j2").read())

    print(f"INTERFACES{interfaces_cfg}\n")
    print(f"NETWORKS{rip_networks}\n")
    # --- Boucle : pour chaque routeur, génère sa configuration et l'écrit dans un fichier ---
    for router_name in routers_data.keys():
        # Remplit le template avec le nom du routeur, ses interfaces et ses réseaux RIP triés
        config = template.render(
            name=router_name,
            interfaces=interfaces_cfg[router_name],
            rip_networks=sorted(rip_networks[router_name])
        )

        # Crée et écrit le fichier de configuration avec le contenu rendu du template
        with open(f"{router_name}.cfg", "w") as f:
            f.write(config)

    print("Configurations générées avec succès.")