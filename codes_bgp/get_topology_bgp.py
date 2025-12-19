"""
Extraction de topologie pour BGP : réutilise get_topology.py puis ajoute:
- Allocation d'ASN séquentielle (65000 + index)
- Calcul des voisins BGP à partir des liens
"""

import json
import ipaddress
from pathlib import Path
from collections import defaultdict

def get_interface_name(adapter, port):
    """Traduit les numéros de port GNS3 en noms d'interfaces Cisco IOS."""
    if adapter == 0:
        return f"FastEthernet{adapter}/{port}"
    else:
        return f"GigabitEthernet{adapter}/{port}"

def extract_topology_bgp(gns3_file, ip_base="2000:1::/64", asn_base=65000, output_dir=None, output_name="topology_bgp.json"):
    """
    Extrait la topologie d'un fichier GNS3 avec ASN et voisins BGP.
    
    Args:
        gns3_file (str): Chemin vers le fichier .gns3
        ip_base (str): Base pour l'adressage IPv6 (défaut: "2000:1::/64")
        asn_base (int): Numéro AS de base (défaut: 65000 -> R1=65001, R2=65002...)
        output_dir (str): Répertoire de sortie
        output_name (str): Nom du fichier de sortie
    
    Returns:
        dict: Les données de topologie extraites avec ASN et voisins
    """
    
    if output_dir is None:
        output_dir = Path(__file__).parent.absolute()
    else:
        output_dir = Path(output_dir)
    
    gns3_path = Path(gns3_file)
    
    print(f"[BGP] Chemin GNS3 : {gns3_path}")
    print(f"[BGP] Fichier existe ? {gns3_path.exists()}")

    # --- 1. CHARGEMENT DE LA TOPOLOGIE DEPUIS GNS3 ---
    try:
        with open(gns3_path, "r") as f:
            gns3_data = json.load(f)
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{gns3_path}' est introuvable.")
        exit(1)

    id_to_name = {}
    routers_list = []

    nodes_data = gns3_data.get("topology", {}).get("nodes", gns3_data.get("nodes", []))
    links_data = gns3_data.get("topology", {}).get("links", gns3_data.get("links", []))

    for node in nodes_data:
        name = node["name"]
        node_id = node["node_id"]
        id_to_name[node_id] = name
        routers_list.append(name)

    print(f"[BGP] Topologie : {len(routers_list)} routeurs ({', '.join(routers_list)})")

    # --- 2. EXTRACTION DES LIENS ---
    links = []

    for link in links_data:
        node_a_data = link["nodes"][0]
        node_b_data = link["nodes"][1]
        
        id_a = node_a_data["node_id"]
        id_b = node_b_data["node_id"]

        if id_a in id_to_name and id_b in id_to_name:
            links.append({
                "a": id_to_name[id_a],
                "a_iface": get_interface_name(node_a_data["adapter_number"], node_a_data["port_number"]),
                "b": id_to_name[id_b],
                "b_iface": get_interface_name(node_b_data["adapter_number"], node_b_data["port_number"])
            })

    print(f"[BGP] Liens détectés : {len(links)}")

    # --- 3. LOGIQUE D'ADRESSAGE IPv6 ---
    base_net = ipaddress.ip_network(ip_base)
    interfaces_cfg = defaultdict(list)
    current_net = base_net

    for link in links:
        a, a_iface_name = link["a"], link["a_iface"]
        b, b_iface_name = link["b"], link["b_iface"]

        ip_a = ipaddress.IPv6Address(int(current_net.network_address) + 1)
        ip_b = ipaddress.IPv6Address(int(current_net.network_address) + 2)

        interfaces_cfg[a].append({
            "name": a_iface_name,
            "ip": str(ip_a),
            "prefix": current_net.prefixlen,
            "link_net": str(current_net.network_address)
        })

        interfaces_cfg[b].append({
            "name": b_iface_name,
            "ip": str(ip_b),
            "prefix": current_net.prefixlen,
            "link_net": str(current_net.network_address)
        })

        # Prochain sous-réseau
        next_net_int = int(current_net.network_address) + current_net.num_addresses
        next_addr = ipaddress.ip_address(next_net_int)
        current_net = ipaddress.ip_network(f"{next_addr}/{current_net.prefixlen}", strict=False)

    # --- 4. ALLOCATION ASN ET CALCUL DES VOISINS ---
    router_to_asn = {}
    router_to_neighbors = defaultdict(list)

    # Allocation ASN séquentielle
    for idx, router_name in enumerate(sorted(routers_list)):
        router_to_asn[router_name] = asn_base + idx + 1

    # Pour chaque lien, ajouter les voisins
    for link in links:
        a, b = link["a"], link["b"]
        
        # Trouver l'IP du routeur B depuis l'interface du routeur A sur ce lien
        for iface_a in interfaces_cfg[a]:
            # On cherche l'interface qui correspond à ce lien (même link_net)
            for iface_b in interfaces_cfg[b]:
                if iface_a["link_net"] == iface_b["link_net"]:
                    router_to_neighbors[a].append({
                        "name": b,
                        "asn": router_to_asn[b],
                        "ip": iface_b["ip"]
                    })
                    router_to_neighbors[b].append({
                        "name": a,
                        "asn": router_to_asn[a],
                        "ip": iface_a["ip"]
                    })
                    break

    # --- 5. EXPORT TOPOLOGY_BGP.JSON ---
    topology_data = {
        "ip_base": ip_base,
        "asn_base": asn_base,
        "routers": [],
        "links": []
    }

    # Ajouter les routeurs avec ASN et voisins
    for router_name in routers_list:
        topology_data["routers"].append({
            "name": router_name,
            "asn": router_to_asn[router_name],
            "interfaces": interfaces_cfg.get(router_name, []),
            "neighbors": router_to_neighbors.get(router_name, [])
        })

    # Ajouter les liens
    for link in links:
        topology_data["links"].append({
            "a": link["a"],
            "a_iface": link["a_iface"],
            "b": link["b"],
            "b_iface": link["b_iface"]
        })

    # Sauvegarder topology_bgp.json
    topology_file = output_dir / output_name
    with open(topology_file, "w", encoding="utf-8") as f:
        json.dump(topology_data, f, indent=2, ensure_ascii=False)
    print(f"[BGP] Topologie exportée : {topology_file}")

    return topology_data
