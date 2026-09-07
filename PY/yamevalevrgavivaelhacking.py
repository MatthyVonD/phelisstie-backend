import os
import re
import psutil

for interface, addrs in psutil.net_if_addrs().items():
    # Filtrar solo adaptadores USB o Ethernet
    if "usb" in interface.lower() or "ethernet" in interface.lower():
        for addr in addrs:
            if addr.family == 2:  # IPv4
                print(f"Interfaz: {interface}")
                print(f"  IP: {addr.address}")
                print(f"  Mascara: {addr.netmask}")
                
                # Obtener Gateway mediante comando del sistema
                cmd_gw = os.popen(f'route print 0.0.0.0 | findstr /i "{addr.address}"').read()
                gateway = re.findall(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', cmd_gw)
                print(f"  Puerta de enlace: {gateway[0] if gateway else 'No asignada'}")
                
                # Obtener DNS mediante comando del sistema filtrado por la interfaz
                cmd_dns = os.popen(f'powershell -Command "(Get-DnsClientServerAddress -InterfaceAlias \'{interface}\' -AddressFamily IPv4).ServerAddresses"').read().strip()
                dns_servers = ", ".join(cmd_dns.splitlines()) if cmd_dns else "No asignados"
                print(f"  DNS: {dns_servers}")
                print("-" * 40)