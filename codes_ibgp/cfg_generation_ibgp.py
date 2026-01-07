import json
import os
import re
from jinja2 import Template


def generate_router_id(router_name):
    match = re.search(r"\d+", router_name)
    if match:
        n = int(match.group())
        return f"{n}.{n}.{n}.{n}"
    return "1.1.1.1"


def cfg_generation_ibgp(topology_path=None, asn=65000, output_dir=None):
    base_dir = os.path.dirname(__file__)
    if topology_path is None:
        topology_path = os.path.join(base_dir, "..", "codes_ospf", "topology.json")
        topology_path = os.path.normpath(topology_path)

    if output_dir is None:
        output_dir = os.path.join(base_dir, "configs")

    os.makedirs(output_dir, exist_ok=True)

    with open(topology_path) as f:
        topo = json.load(f)

    routers = topo.get("routers", [])
    routers_data = {r["name"]: r for r in routers}

    # build basic neighbor list: full-mesh using each router's first interface IP
    neighbors_map = {}
    for r in routers:
        name = r["name"]
        # first iface ip
        ifaces = r.get("interfaces", [])
        ip = ifaces[0]["ip"] if ifaces else None
        neighbors_map[name] = ip

    template_path = os.path.join(base_dir, "router_ibgp.j2")
    template = Template(open(template_path).read())

    for router in routers:
        name = router["name"]
        router_id = generate_router_id(name)

        # neighbors: all other routers (iBGP full mesh) using their first interface IPs
        neighbors = []
        for other_name, other_ip in neighbors_map.items():
            if other_name == name or other_ip is None:
                continue
            neighbors.append({"name": other_name, "ip": other_ip})

        config = template.render(
            name=name,
            interfaces=router.get("interfaces", []),
            router_id=router_id,
            asn=asn,
            neighbors=neighbors,
        )

        out_file = os.path.join(output_dir, f"{name}.cfg")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(config)

        print(f"[iBGP] Config générée : {out_file}")

    print("[iBGP] Génération terminée.")


if __name__ == "__main__":
    # Example: will use codes_ospf/topology.json by default
    cfg_generation_ibgp()
