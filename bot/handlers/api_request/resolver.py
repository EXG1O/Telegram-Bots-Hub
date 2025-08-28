from aiohttp import ThreadedResolver
from aiohttp.abc import ResolveResult

from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
    ip_address,
    ip_network,
)
import socket


class SafeResolver(ThreadedResolver):
    private_networks: list[IPv4Network | IPv6Network] = [
        ip_network('127.0.0.0/8'),
        ip_network('10.0.0.0/8'),
        ip_network('172.16.0.0/12'),
        ip_network('192.168.0.0/16'),
        ip_network('169.254.0.0/16'),
        ip_network('::1/128'),
        ip_network('fc00::/7'),
        ip_network('fe80::/10'),
    ]

    async def resolve(
        self,
        hostname: str,
        port: int = 0,
        family: socket.AddressFamily = socket.AF_INET,
    ) -> list[ResolveResult]:
        hosts: list[ResolveResult] = await super().resolve(hostname, port, family)
        safe_hosts: list[ResolveResult] = []

        for host in hosts:
            host_ip: IPv4Address | IPv6Address = ip_address(host['host'])

            for private_network in self.private_networks:
                if host_ip in private_network:
                    break
            else:
                safe_hosts.append(host)

        return safe_hosts
