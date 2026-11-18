import ipaddress
import socket
from collections.abc import Callable
from dataclasses import dataclass
from urllib.parse import urlsplit

from app.ports.mcp import AddressRefused

Resolver = Callable[..., list[tuple]]

# DNS64 hides an IPv4 address in the last 32 bits; the guard judges that address.
_NAT64 = ipaddress.ip_network("64:ff9b::/96")


@dataclass(frozen=True)
class Target:
    """A URL whose host was resolved and checked once. Connect to `ip`, never to
    `host` again: a second lookup could answer differently (DNS rebinding)."""

    host: str
    ip: str
    port: int
    path: str

    @property
    def url(self) -> str:
        literal = f"[{self.ip}]" if ":" in self.ip else self.ip
        return f"https://{literal}:{self.port}{self.path}"


def _public(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped:
            ip = ip.ipv4_mapped
        elif ip in _NAT64:
            ip = ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
    return ip.is_global


def check(url: str, resolve: Resolver = socket.getaddrinfo) -> Target:
    """HTTPS only, no credentials in the URL, and every address the host resolves to
    must be public. Raises AddressRefused."""
    try:
        parts = urlsplit(url)
        host, port = parts.hostname, parts.port or 443
    except ValueError as exc:
        raise AddressRefused("not a valid URL") from exc
    if parts.scheme != "https" or not host or parts.username or parts.password:
        raise AddressRefused("not a plain https URL")
    try:
        found = resolve(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise AddressRefused("host does not resolve") from exc
    addresses = [info[4][0] for info in found]
    try:
        safe = bool(addresses) and all(_public(address) for address in addresses)
    except ValueError:
        safe = False
    if not safe:
        raise AddressRefused("host is not a public address")
    path = parts.path or "/"
    if parts.query:
        path = f"{path}?{parts.query}"
    return Target(host=host, ip=addresses[0], port=port, path=path)
