#!/usr/bin/env python3
"""
Script de validation des configurations BGP générées
"""
import os
import re

def validate_config(filename):
    """Valide une configuration de routeur"""
    print(f"\n{'='*60}")
    print(f"Validation de {filename}")
    print(f"{'='*60}")
    
    if not os.path.exists(filename):
        print(f"❌ Fichier introuvable: {filename}")
        return False
    
    with open(filename, 'r') as f:
        content = f.read()
    
    checks = {
        "hostname": r"hostname \w+",
        "ipv6 unicast-routing": r"ipv6 unicast-routing",
        "interface loopback": r"interface Loopback0",
        "ipv6 address loopback": r"ipv6 address 2001:db8::\d+/128",
        "router bgp": r"router bgp \d+",
        "bgp router-id": r"bgp router-id \d+\.\d+\.\d+\.\d+",
        "neighbor bgp": r"neighbor 2001:db8::",
        "address-family ipv6": r"address-family ipv6 unicast",
        "neighbor activate": r"neighbor .* activate",
        "redistribute": r"redistribute connected"
    }
    
    results = {}
    for check_name, pattern in checks.items():
        if re.search(pattern, content):
            print(f"✅ {check_name}")
            results[check_name] = True
        else:
            print(f"❌ {check_name}")
            results[check_name] = False
    
    # Statistiques
    interfaces = len(re.findall(r'^interface ', content, re.MULTILINE))
    neighbors = len(re.findall(r'neighbor .* remote-as', content, re.MULTILINE))
    ipv6_addrs = len(re.findall(r'ipv6 address 2001:db8:', content))
    
    print(f"\n📊 Statistiques:")
    print(f"   - Interfaces: {interfaces}")
    print(f"   - Voisins BGP: {neighbors}")
    print(f"   - Adresses IPv6: {ipv6_addrs}")
    
    success_rate = sum(results.values()) / len(results) * 100
    print(f"\n{'✅' if success_rate >= 80 else '⚠️'} Taux de réussite: {success_rate:.1f}%")
    
    return success_rate >= 80

def main():
    configs_dir = "configs"
    
    print("🔍 Validation des configurations BGP")
    print("="*60)
    
    if not os.path.exists(configs_dir):
        print(f"❌ Dossier {configs_dir}/ introuvable")
        return
    
    config_files = sorted([f for f in os.listdir(configs_dir) if f.endswith('.cfg')])
    
    if not config_files:
        print(f"❌ Aucun fichier .cfg trouvé dans {configs_dir}/")
        return
    
    print(f"📁 Fichiers trouvés: {len(config_files)}")
    
    results = {}
    for config_file in config_files:
        filepath = os.path.join(configs_dir, config_file)
        results[config_file] = validate_config(filepath)
    
    # Résumé final
    print("\n" + "="*60)
    print("📋 RÉSUMÉ FINAL")
    print("="*60)
    for config_file, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {config_file}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\n🎯 Total: {passed}/{total} configurations valides")
    
    if passed == total:
        print("✅ Toutes les configurations sont valides!")
    else:
        print(f"⚠️ {total - passed} configuration(s) nécessite(nt) des corrections")

if __name__ == "__main__":
    main()
