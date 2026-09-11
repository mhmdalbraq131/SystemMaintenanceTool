"""Windows Security status and control service.

Reads Defender, Firewall, and Security Center info via Windows APIs.
Never disables protection without explicit user confirmation.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field


@dataclass
class SecurityData:
    """Security status snapshot."""
    defender_available: bool = False
    defender_status: str = "غير متاح"
    real_time_protection: bool | None = None
    antivirus_up_to_date: bool | None = None
    firewall_enabled: bool | None = None
    firewall_status: str = "غير معروف"
    security_center_warnings: list[str] = field(default_factory=list)


def collect_security_data() -> SecurityData:
    """Gather security status from the live system."""
    data = SecurityData()

    # Defender status via sc query
    try:
        result = subprocess.run(
            ["sc", "query", "WinDefend"],
            capture_output=True, text=True, timeout=10,
            encoding="cp1256", errors="replace"
        )
        if result.returncode == 0:
            data.defender_available = True
            if "RUNNING" in result.stdout:
                data.defender_status = "قيد التشغيل"
            elif "STOPPED" in result.stdout:
                data.defender_status = "متوقف"
            else:
                data.defender_status = "غير معروف"
    except Exception:
        data.defender_available = False

    # Real-time protection via PowerShell
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-MpComputerStatus | Select-Object -Property RealTimeProtectionEnabled, AntivirusSignatureLastUpdated | ConvertTo-Json"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        if result.returncode == 0 and result.stdout.strip():
            import json
            status = json.loads(result.stdout)
            data.real_time_protection = status.get("RealTimeProtectionEnabled")
            # Check if signature updated within last 24h
            last_updated = status.get("AntivirusSignatureLastUpdated")
            if last_updated:
                from datetime import datetime, timezone
                try:
                    updated_time = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
                    delta = datetime.now(timezone.utc) - updated_time
                    data.antivirus_up_to_date = delta.days < 1
                except Exception:
                    data.antivirus_up_to_date = None
    except Exception:
        pass

    # Firewall status
    try:
        result = subprocess.run(
            ["netsh", "advfirewall", "show", "currentprofile", "state"],
            capture_output=True, text=True, timeout=10,
            encoding="cp1256", errors="replace"
        )
        if result.returncode == 0:
            if "ON" in result.stdout.upper() or "مشتعل" in result.stdout:
                data.firewall_enabled = True
                data.firewall_status = "مفعّل"
            elif "OFF" in result.stdout.upper() or "مطفي" in result.stdout:
                data.firewall_enabled = False
                data.firewall_status = "معطّل"
    except Exception:
        pass

    # Security Center via WMI
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntivirusProduct | Select-Object displayName, productState | ConvertTo-Json"],
            capture_output=True, text=True, timeout=15,
            encoding="utf-8", errors="replace"
        )
        if result.returncode == 0 and result.stdout.strip():
            import json
            products = json.loads(result.stdout)
            if isinstance(products, dict):
                products = [products]
            for p in products:
                state = p.get("productState", 0)
                # Bit flags interpretation (simplified)
                if state & 0x10:
                    data.security_center_warnings.append(f"{p.get('displayName', '')}: محدّث ونشط")
                else:
                    data.security_center_warnings.append(f"{p.get('displayName', '')}: قد يحتاج انتباه")
    except Exception:
        pass

    return data


# ── Defender Scans ────────────────────────────────────────────────────────

def start_quick_scan() -> tuple[bool, str]:
    """Start a Defender quick scan."""
    return _defender_cmd("Start-MpScan -ScanType QuickScan", "فحص سريع")


def start_full_scan() -> tuple[bool, str]:
    """Start a Defender full scan."""
    return _defender_cmd("Start-MpScan -ScanType FullScan", "فحص كامل")


def start_custom_scan(path: str) -> tuple[bool, str]:
    """Start a Defender custom scan on a specific path."""
    return _defender_cmd(f'Start-MpScan -ScanType CustomScan -ScanPath "{path}"', f"فحص مخصص: {path}")


def _defender_cmd(ps_cmd: str, label: str) -> tuple[bool, str]:
    """Execute a Defender PowerShell command."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=60,
            encoding="utf-8", errors="replace"
        )
        if result.returncode == 0:
            return True, f"تم بدء {label}"
        return False, f"فشل بدء {label}: {result.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return False, f"انتهت مهلة {label}"
    except Exception as e:
        return False, f"خطأ: {e}"
