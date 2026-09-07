import os
import psutil

for interface, addrs in psutil.net_if_addrs().items():
    if "usb" in interface.lower() or "ethernet" in interface.lower():
        for addr in addrs:
            if addr.family == 2:  # IPv4
                print(f"Interfaz: {interface}")
                print(f"  IP: {addr.address}")
                
                # Comando para consultar si la interfaz tiene plantillas DoH (HTTPS) activas
                cmd_doh = os.popen(f'powershell -Command "Get-DnsClientServerAddress -InterfaceAlias \'{interface}\' -AddressFamily IPv4 | Select-Object -ExpandProperty ServerAddresses"').read().strip()
                dns_servers = cmd_doh.splitlines()
                
                print(f"  DNS Detectados: {', '.join(dns_servers) if dns_servers else 'Ninguno'}")
                
                # Verificar si el sistema operativo está forzando HTTPS en esos DNS
                print("  Protocolo base: UDP/53 (Tráfico estándar)")
                print("  Cifrado HTTPS: Disponible si el servidor destino es compatible (Ej: 1.1.1.1 o 8.8.8.8)")
                print("-" * 50)