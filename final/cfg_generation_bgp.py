import json
from jinja2 import Template
import re

def generate_router_id(router_name):
    """
    Génère un router-id IPv4 à partir du nom du routeur
    Ex: R1 -> 1.1.1.1
    """
    match = re.search(r"\d+", router_name)
    if match:
        n = int(match.group())
        return f"{n}.{n}.{n}.{n}"
    else:
        return "1.1.1.1"

def convert_ipv4_loopback_to_ipv6(ip, router_num):
    """
    Convertit une adresse IPv4 de loopback en IPv6
    Ex: 10.0.1.1 -> 2001:db8::1
    """
    if ip and ip.startswith("10.0."):
        return f"2001:db8::{router_num}"
    return ip

def generate_ripng_config(interfaces):
    """
    Génère la configuration RIPng pour les interfaces
    """
    config = "\n!\nipv6 router rip RIPNG\n redistribute connected\n"
    for iface in interfaces:
        if iface["name"] != "Loopback0":
            config += f"\n!\ninterface {iface['name']}\n ipv6 rip RIPNG enable\n no shutdown\n"
    return config

def generate_ospfv3_config(router_name, interfaces):
    """
    Génère la configuration OSPFv3 pour les interfaces
    """
    match = re.search(r"\d+", router_name)
    router_id = int(match.group()) if match else 1
    
    config = f"\n!\nipv6 router ospf 1\n router-id {router_id}.{router_id}.{router_id}.{router_id}\n redistribute connected subnets\n"
    for iface in interfaces:
        if iface["name"] != "Loopback0":
            config += f"\n!\ninterface {iface['name']}\n ipv6 ospf 1 area 0\n no shutdown\n"
    # Ajouter loopback aussi pour OSPF
    config += f"\n!\ninterface Loopback0\n ipv6 ospf 1 area 0\n"
    return config


def cfg_generation_bgp(topology, output_dir="."):
    with open(topology) as f:
        topo = json.load(f)

    routers_data = {r["name"]: r for r in topo["routers"]}
    
    template = Template(open("router_bgp.j2").read())
    
    for router_name, router in routers_data.items():
        router_id = generate_router_id(router_name)
        
        # Extraire le numéro du routeur
        match = re.search(r"\d+", router_name)
        router_num = int(match.group()) if match else 1
        
        # Convertir les interfaces loopback IPv4 en IPv6
        interfaces = []
        for iface in router["interfaces"]:
            iface_copy = iface.copy()
            if iface["name"] == "Loopback0" and iface["ip"].startswith("10.0."):
                iface_copy["ip"] = convert_ipv4_loopback_to_ipv6(iface["ip"], router_num)
                iface_copy["prefix"] = 128
            interfaces.append(iface_copy)
        
        # Convertir les adresses des voisins IPv4 loopback en IPv6
        neighbors = []
        for neighbor in router["neighbors"]:
            neighbor_copy = neighbor.copy()
            neighbor_ip = neighbor_copy.get("neighbor", "")
            if neighbor_ip.startswith("10.0."):
                # Extraire le dernier octet pour le numéro du routeur voisin
                parts = neighbor_ip.split(".")
                neighbor_num = int(parts[-1])
                neighbor_copy["neighbor"] = f"2001:db8::{neighbor_num}"
            neighbors.append(neighbor_copy)

        config = template.render(
            name=router_name,
            asn=router["asn"],
            router_id=router_id,
            interfaces=interfaces,
            neighbors=neighbors
        )
        
        # Ajouter IGP (RIP ou OSPF)
        igp = router.get("igp", "").lower()
        if igp == "rip":
            config += generate_ripng_config(interfaces)
        elif igp == "ospf":
            config += generate_ospfv3_config(router_name, interfaces)
        
        output_file = f"{output_dir}/{router_name}.cfg"
        with open(output_file, "w") as f:
            f.write(config)
        
        print(f"[BGP+IGP] Config générée : {output_file}")
    
    print("[BGP+IGP] Configurations BGP+IGP générées avec succès.")


cfg_generation_bgp("topology.json", "configs")