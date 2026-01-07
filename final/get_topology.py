import json
import ipaddress
from pathlib import Path
from collections import defaultdict

# --- FONCTION UTILITAIRE : Traduction GNS3 -> Cisco ---
def get_interface_name(adapter, port):
    """
    Traduit les numéros de port GNS3 en noms d'interfaces Cisco IOS.
    A adapter selon le modèle de routeur (ici optimisé pour c7200).
    """
    # Sur un c7200, l'adaptateur 0 est souvent le FastEthernet intégré
    if adapter == 0:
        return f"FastEthernet{adapter}/{port}"
    # Les adaptateurs suivants (1, 2...) sont souvent des modules Gigabit
    else:
        return f"GigabitEthernet{adapter}/{port}"

# --- FONCTION PRINCIPALE ---
def extract_topology(gns3_file, ip_base="2000:1::/64", output_dir=None, output_name="topology.json"):
    """
    Extrait la topologie d'un fichier GNS3 et génère un fichier topology.json
    
    Args:
        gns3_file (str): Chemin vers le fichier .gns3
        ip_base (str): Base pour l'adressage IPv6 (défaut: "2000:1::/64")
        output_dir (str): Répertoire de sortie (défaut: répertoire du script)
        output_name (str): Nom du fichier de sortie (défaut: "topology.json")
    
    Returns:
        dict: Les données de topologie extraites
    """
    
    # Configuration des chemins
    if output_dir is None:
        output_dir = Path(__file__).parent.absolute()
    else:
        output_dir = Path(output_dir)
    
    gns3_path = Path(gns3_file)
    
    print(f"Chemin GNS3 utilisé : {gns3_path}")
    print(f"Fichier existe ? {gns3_path.exists()}")

    # --- 1. CHARGEMENT DE LA TOPOLOGIE DEPUIS GNS3 ---
    try:
        with open(gns3_path, "r") as f:
            gns3_data = json.load(f)
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{gns3_path}' est introuvable.")
        exit(1)

    # Création d'un dictionnaire pour retrouver le nom d'un routeur via son ID unique
    id_to_name = {}
    routers_list = []

    # GNS3 stocke parfois les nœuds directement sous la racine ou sous "topology"
    nodes_data = gns3_data.get("topology", {}).get("nodes", gns3_data.get("nodes", []))
    links_data = gns3_data.get("topology", {}).get("links", gns3_data.get("links", []))

    print(f"DEBUG - Structure GNS3: clés racine = {list(gns3_data.keys())}")
    print(f"DEBUG - Nombre de nœuds trouvés : {len(nodes_data)}")
    print(f"DEBUG - Nombre de liens trouvés : {len(links_data)}")

    for node in nodes_data:
        name = node["name"]
        node_id = node["node_id"]
        id_to_name[node_id] = name
        routers_list.append(name)

    print(f"Topologie détectée : {len(routers_list)} routeurs ({', '.join(routers_list)})")

    # --- 2. EXTRACTION DES LIENS ET CONVERSION ---
    links = []

    for link in links_data:
        node_a_data = link["nodes"][0]
        node_b_data = link["nodes"][1]
        
        id_a = node_a_data["node_id"]
        id_b = node_b_data["node_id"]

        # On vérifie que les deux bouts sont bien des routeurs connus
        if id_a in id_to_name and id_b in id_to_name:
            links.append({
                "a": id_to_name[id_a],
                "a_iface": get_interface_name(node_a_data["adapter_number"], node_a_data["port_number"]),
                "b": id_to_name[id_b],
                "b_iface": get_interface_name(node_b_data["adapter_number"], node_b_data["port_number"])
            })

    print(f"Liens détectés : {len(links)} liens actifs.")

    # --- 3. LOGIQUE D'ADRESSAGE ---
    base_net = ipaddress.ip_network(ip_base)
    interfaces_cfg = defaultdict(list)
    rip_networks = defaultdict(set)
    current_net = base_net

    for link in links:
        a, a_iface_name = link["a"], link["a_iface"]
        b, b_iface_name = link["b"], link["b_iface"]

        ip_a = ipaddress.IPv6Address(int(current_net.network_address) + 1)
        ip_b = ipaddress.IPv6Address(int(current_net.network_address) + 2)

        # Configuration pour le routeur A
        interfaces_cfg[a].append({
            "name": a_iface_name,
            "ip": str(ip_a),
            "prefix": current_net.prefixlen
        })
        rip_networks[a].add(str(current_net.network_address))

        # Configuration pour le routeur B
        interfaces_cfg[b].append({
            "name": b_iface_name,
            "ip": str(ip_b),
            "prefix": current_net.prefixlen
        })
        rip_networks[b].add(str(current_net.network_address))

        # Calcul du prochain sous-réseau
        next_net_int = int(current_net.network_address) + current_net.num_addresses
        next_addr = ipaddress.ip_address(next_net_int)
        current_net = ipaddress.ip_network(f"{next_addr}/{current_net.prefixlen}", strict=False)

    # --- 3b. EXPORT TOPOLOGY.JSON ---
    topology_data = {
        "ip_base": ip_base,
        "routers": [],
        "links": []
    }

    # Ajouter les routeurs
    for router_name in routers_list:
        topology_data["routers"].append({
            "name": router_name,
            "interfaces": interfaces_cfg.get(router_name, []),
            "rip_networks": sorted(rip_networks.get(router_name, []))
        })

    # Ajouter les liens
    for link in links:
        topology_data["links"].append({
            "a": link["a"],
            "a_iface": link["a_iface"],
            "b": link["b"],
            "b_iface": link["b_iface"]
        })

    # Sauvegarder topology.json
    topology_file = output_dir / output_name
    with open(topology_file, "w", encoding="utf-8") as f:
        json.dump(topology_data, f, indent=2, ensure_ascii=False)
    print(f"Topologie exportée : {topology_file}")

    print(f"\nTerminé ! La topologie a été extraite depuis {gns3_path}")
    
    return topology_data