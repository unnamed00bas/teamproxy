"""WireGuard key generation and config templating.

On the first stage we manage WireGuard purely through data + rendered config
templates (no kernel/netlink integration). Keys are generated server-side; the
private key is returned exactly once to the operator and never persisted in
plaintext — only the public key and a secret reference are stored.

Keys are standard Curve25519 (X25519), base64-encoded — byte-for-byte
compatible with ``wg genkey`` / ``wg pubkey``.
"""

from __future__ import annotations

import base64
import ipaddress
from collections.abc import Iterable

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)


def generate_keypair() -> tuple[str, str]:
    """Return (private_key_b64, public_key_b64)."""
    private = X25519PrivateKey.generate()
    private_raw = private.private_bytes(
        Encoding.Raw, PrivateFormat.Raw, NoEncryption()
    )
    public_raw = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return (
        base64.b64encode(private_raw).decode(),
        base64.b64encode(public_raw).decode(),
    )


def hub_tunnel_ip(subnet: str) -> str:
    """The hub's own tunnel address — the first host in the subnet (e.g. .1)."""
    net = ipaddress.ip_network(subnet, strict=False)
    return str(next(net.hosts()))


def allocate_tunnel_ip(subnet: str, used: Iterable[str]) -> str:
    """Return the next free host IP in ``subnet``.

    The hub itself occupies the first host address, so it is always reserved.
    Any address already present in ``used`` (with or without a ``/prefix``
    suffix) is skipped. Raises ``ValueError`` when the subnet is exhausted.
    """
    net = ipaddress.ip_network(subnet, strict=False)
    taken = {str(ipaddress.ip_address(ip.split("/")[0])) for ip in used if ip}
    taken.add(hub_tunnel_ip(subnet))
    for host in net.hosts():
        candidate = str(host)
        if candidate not in taken:
            return candidate
    raise ValueError(f"No free tunnel IP available in {subnet}")


def render_peer_config(
    *,
    private_key: str,
    address: str | None,
    server_public_key: str = "<HUB_PUBLIC_KEY>",
    server_endpoint: str = "<VPS_ENDPOINT>:51820",
    allowed_ips: list[str] | None = None,
    keepalive: int = 25,
) -> str:
    """Render a client-side ``wg-quick`` config for a site gateway peer."""
    allowed = ", ".join(allowed_ips or ["0.0.0.0/0"])
    addr_line = f"Address = {address}\n" if address else ""
    return (
        "[Interface]\n"
        f"PrivateKey = {private_key}\n"
        f"{addr_line}"
        "\n"
        "[Peer]\n"
        f"PublicKey = {server_public_key}\n"
        f"Endpoint = {server_endpoint}\n"
        f"AllowedIPs = {allowed}\n"
        f"PersistentKeepalive = {keepalive}\n"
    )


def render_gateway_bootstrap(site) -> str:  # noqa: ANN001 - duck-typed Site
    """Render an operator-facing bootstrap snippet for a site gateway.

    This is intentionally a documented template, not an executable installer,
    so the operator can review before running it on the gateway node.
    """
    subnet = site.wg_tunnel_subnet or "10.10.0.0/24"
    local = ", ".join(site.local_subnets or [])
    return (
        f"# Gateway bootstrap for site: {site.name} ({site.slug})\n"
        f"# Tunnel subnet: {subnet}\n"
        f"# Local subnets: {local or '<none configured>'}\n"
        "#\n"
        "# 1. Install WireGuard:    apt-get install -y wireguard\n"
        "# 2. Create a peer in the control plane (VPN / Peers) and download the\n"
        "#    generated wg-quick config into /etc/wireguard/wg0.conf\n"
        "# 3. Enable the tunnel:    systemctl enable --now wg-quick@wg0\n"
        "# 4. Verify handshake:     wg show\n"
        "#\n"
        "# The control plane will mark the site online once the peer reports a\n"
        "# recent handshake.\n"
    )
