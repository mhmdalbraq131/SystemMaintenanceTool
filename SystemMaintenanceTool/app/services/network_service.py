"""Real-time network data collection and diagnostic tools.

Uses psutil for stats and subprocess for diagnostic commands.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore


@dataclass
class AdapterInfo:
    """Network adapter static info."""
    name: str = ""
    status: str = "غير متصل"
    mac: str = ""
    ipv4: str = ""
    ipv6: str = ""
    gateway: str = ""
    dns: str = ""
    link_speed_mbps: int | None = None


@dataclass
class NetworkStats:
    """Current network throughput."""
    download_bytes_sec: float = 0.0
    upload_bytes_sec: float = 0.0
    packets_sent: int = 0
    packets_recv: int = 0
    errors_in: int = 0
    errors_out: int = 0
    drops_in: int = 0
    drops_out: int = 0


@dataclass
class NetworkData:
    """Full network snapshot."""
    adapters: list[AdapterInfo] = field(default_factory=list)
    stats: NetworkStats = field(default_factory=NetworkStats)


def collect_network_data(prev_counters: dict | None = None,
                          interval: float = 1.0) -> NetworkData:
    """Gather network metrics from the live system."""
    if psutil is None:
        return NetworkData()

    data = NetworkData()

    # Adapters
    addrs = psutil.net_if_addrs()
    stats_if = psutil.net_if_stats()
    for name, addr_list in addrs.items():
        adapter = AdapterInfo(name=name)
        link_stat = stats_if.get(name)
        if link_stat:
            adapter.status = "متصل" if link_stat.isup else "غير متصل"
            adapter.link_speed_mbps = link_stat.speed if link_stat.speed > 0 else None
        for addr in addr_list:
            if addr.family == psutil.AF_LINK:
                adapter.mac = addr.address
            elif addr.family == 2:  # AF_INET
                adapter.ipv4 = addr.address
            elif addr.family == 30:  # AF_INET6
                adapter.ipv6 = addr.address
        gateway, dns = _get_gateway_dns(name)
        adapter.gateway = gateway
        adapter.dns = dns
        data.adapters.append(adapter)

    # Stats
    counters = psutil.net_io_counters()
    if counters and prev_counters:
        data.stats = NetworkStats(
            download_bytes_sec=round((counters.bytes_recv - prev_counters.get("bytes_recv", 0)) / interval, 2),
            upload_bytes_sec=round((counters.bytes_sent - prev_counters.get("bytes_sent", 0)) / interval, 2),
            packets_sent=counters.packets_sent,
            packets_recv=counters.bytes_recv,
            errors_in=counters.errin,
            errors_out=counters.errout,
            drops_in=counters.dropin,
            drops_out=counters.dropout,
        )

    return data


def get_network_counters() -> dict | None:
    """Return cumulative counters for rate calculation."""
    if psutil is None:
        return None
    c = psutil.net_io_counters()
    return {"bytes_recv": c.bytes_recv, "bytes_sent": c.bytes_sent} if c else None


def _get_gateway_dns(adapter_name: str) -> tuple[str, str]:
    """Read default gateway and DNS for adapter via subprocess."""
    gateway, dns = "", ""
    try:
        out = subprocess.run(
            ["ipconfig", "/all"],
            capture_output=True, text=True, timeout=10,
            encoding="cp1256", errors="replace"
        ).stdout
        # Parse ipconfig output (simplified)
        lines = out.splitlines()
        in_adapter = False
        for line in lines:
            if adapter_name.lower() in line.lower():
                in_adapter = True
                continue
            if in_adapter and line.strip() == "":
                in_adapter = False
            if in_adapter:
                if "Default Gateway" in line or "البوابة" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        gateway = parts[-1].strip()
                if "DNS Servers" in line or "خوادم DNS" in line:
                    parts = line.split(":")
                    if len(parts) > 1:
                        dns = parts[-1].strip()
    except Exception:
        pass
    return gateway, dns


# ── Diagnostic Tools ─────────────────────────────────────────────────────

def run_ping(host: str = "8.8.8.8", count: int = 4) -> str:
    """Execute ping and return output."""
    return _run_cmd(["ping", "-n", str(count), host])


def run_tracert(host: str = "8.8.8.8", hops: int = 30) -> str:
    """Execute tracert and return output."""
    return _run_cmd(["tracert", "-h", str(hops), host])


def run_nslookup(domain: str = "google.com") -> str:
    """Execute nslookup and return output."""
    return _run_cmd(["nslookup", domain])


def run_netstat() -> str:
    """Execute netstat and return output."""
    return _run_cmd(["netstat", "-ano"])


def run_arp() -> str:
    """Execute arp -a and return output."""
    return _run_cmd(["arp", "-a"])


def run_route() -> str:
    """Execute route print and return output."""
    return _run_cmd(["route", "print"])


def flush_dns() -> tuple[bool, str]:
    """Flush DNS cache. Returns (success, output)."""
    out = _run_cmd(["ipconfig", "/flushdns"])
    return ("successfully" in out.lower() or "بنجاح" in out, out)


def release_ip() -> tuple[bool, str]:
    """Release IP address."""
    out = _run_cmd(["ipconfig", "/release"])
    return (True, out)


def renew_ip() -> tuple[bool, str]:
    """Renew IP address."""
    out = _run_cmd(["ipconfig", "/renew"])
    return (True, out)


def _run_cmd(cmd: list[str], timeout: int = 60) -> str:
    """Run a subprocess command and return its output."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            encoding="cp1256", errors="replace"
        )
        return result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return f"انتهت المهلة الزمنية للأمر ({timeout}s)"
    except FileNotFoundError:
        return f"الأمر غير متاح: {cmd[0]}"
    except Exception as e:
        return f"خطأ: {e}"
