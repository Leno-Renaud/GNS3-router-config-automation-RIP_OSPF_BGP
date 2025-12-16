import json
import ipaddress
from jinja2 import Template
from collections import defaultdict

# --- Charger la topologie ---
with open("topology.json") as f:
    topo = json.load(f)

routers_data = {r["name"]: r for r in topo["routers"]}
links = topo["links"]
base_net = ipaddress.ip_network(topo["ip_base"])

# --- Structures internes ---
interfaces_cfg = defaultdict(list)
rip_networks = defaultdict(set)

current_net = base_net

# --- Génération IP pour chaque lien ---
for link in links:
    a, a_iface_name = link["a"], link["a_iface"]
    b, b_iface_name = link["b"], link["b_iface"]

    hosts = list(current_net.hosts())
    ip_a = hosts[0]
    ip_b = hosts[1]

    # Interfaces
    interfaces_cfg[a].append({
        "name": a_iface_name,
        "ip": str(ip_a),
        "mask": str(current_net.netmask)
    })
    interfaces_cfg[b].append({
        "name": b_iface_name,
        "ip": str(ip_b),
        "mask": str(current_net.netmask)
    })

    # RIP networks
    rip_networks[a].add(str(current_net.network_address))
    rip_networks[b].add(str(current_net.network_address))

    # Prochain subnet
    current_net = ipaddress.ip_network(
        int(current_net.network_address) + current_net.num_addresses
    ).supernet(new_prefix=current_net.prefixlen)

# --- Charger le template ---
template = Template(open("router_rip.j2").read())

# --- Génération des configs ---
for router_name in routers_data.keys():
    config = template.render(
        name=router_name,
        interfaces=interfaces_cfg[router_name],
        rip_networks=sorted(rip_networks[router_name])
    )

    with open(f"{router_name}.cfg", "w") as f:
        f.write(config)

print("Configurations générées avec succès.")