import json
import re
from pathlib import Path
from typing import Dict
from jinja2 import Template

from ospfv3_gen import build_ospf_config, generate_ipv6_addresses

BASE = Path(__file__).parent


def load_template(name: str) -> Template:
    return Template((BASE / name).read_text())


def router_id_from_name(name: str) -> str:
    digits = "".join(ch for ch in name if ch.isdigit()) or "1"
    n = int(digits)
    return f"{n}.{n}.{n}.{n}"


def convert_loopback_to_ipv6(ip: str, router_num: int) -> str:
    if ip.startswith("10.0."):
        return f"2001:db8::{router_num}"
    return ip


def normalize_interfaces(router: dict) -> list:
    """Clone interfaces and normalize loopback IPv6 /128."""
    match = re.search(r"\d+", router.get("name", ""))
    router_num = int(match.group()) if match else 1

    interfaces = []
    for iface in router.get("interfaces", []):
        item = iface.copy()
        if item["name"].lower().startswith("loopback") and item.get("ip", "").startswith("10.0."):
            item["ip"] = convert_loopback_to_ipv6(item["ip"], router_num)
            item["prefix"] = 128
        interfaces.append(item)
    return interfaces


def normalize_neighbors(neighbors: list) -> list:
    """Convert iBGP neighbors on IPv4 loopbacks to IPv6 loopbacks."""
    normalized = []
    for nb in neighbors:
        item = nb.copy()
        addr = item.get("neighbor") or item.get("ip")
        if addr and addr.startswith("10.0."):
            last = int(addr.split(".")[-1])
            item_key = "neighbor" if "neighbor" in item else "ip"
            item[item_key] = f"2001:db8::{last}"
        normalized.append(item)
    return normalized


def generate_bgp_configs(topo: dict) -> Dict[str, str]:
    tpl_bgp = load_template("router_bgp.j2")
    result: Dict[str, str] = {}

    for router in topo.get("routers", []):
        interfaces = normalize_interfaces(router)
        neighbors = normalize_neighbors(router.get("neighbors", []))
        cfg = tpl_bgp.render(
            name=router["name"],
            asn=router["asn"],
            router_id=router_id_from_name(router["name"]),
            interfaces=interfaces,
            neighbors=neighbors,
        )
        result[router["name"]] = cfg
    return result


def generate_rip_configs(topo: dict) -> Dict[str, str]:
    tpl_rip = load_template("router_rip.j2")
    result: Dict[str, str] = {}

    for router in topo.get("routers", []):
        if router.get("igp", "").lower() != "rip":
            continue
        interfaces = [i for i in router.get("interfaces", []) if not i["name"].lower().startswith("loopback")]
        cfg = tpl_rip.render(name=router["name"], interfaces=interfaces)
        result[router["name"]] = cfg
    return result


def generate_ospf_configs(topo: dict) -> Dict[str, str]:
    result: Dict[str, str] = {}
    ipv6_assignments = generate_ipv6_addresses(topo)

    for router in topo.get("routers", []):
        if router.get("igp", "").lower() != "ospf":
            continue
        cfg = build_ospf_config(router["name"], topo, ipv6_assignments)
        result[router["name"]] = cfg
    return result


def generate_all_configs(topo: dict) -> Dict[str, str]:
    bgp_cfg = generate_bgp_configs(topo)
    rip_cfg = generate_rip_configs(topo)
    ospf_cfg = generate_ospf_configs(topo)

    merged: Dict[str, str] = {}
    for name, cfg in bgp_cfg.items():
        parts = [cfg]
        if name in rip_cfg:
            parts.append(rip_cfg[name])
        if name in ospf_cfg:
            parts.append(ospf_cfg[name])
        merged[name] = "\n!\n".join(parts)
    return merged


def main() -> Dict[str, str]:
    topo = json.loads((BASE / "topology.json").read_text())
    configs = generate_all_configs(topo)

    out_dir = BASE / "configs"
    out_dir.mkdir(exist_ok=True)
    for name, cfg in configs.items():
        (out_dir / f"{name}.cfg").write_text(cfg)
        print(f"Config générée : {out_dir/f'{name}.cfg'}")
    return configs


if __name__ == "__main__":
    main()
