"""Centralized diagnostic system.

Runs real checks on CPU, RAM, Disk, Network, Security, etc.
Never fabricates results. Returns Passed / Warning / Critical / Unknown.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore

from app.services import cpu_service, ram_service, disk_service, network_service, security_service
from config.settings import (
    CPU_ALERT_THRESHOLD,
    RAM_ALERT_THRESHOLD,
    DISK_ALERT_THRESHOLD,
    DISK_SPACE_WARNING_GB,
)


class DiagnosticStatus(str, Enum):
    PASSED = " Passed"
    PASSED_AR = "سليم"
    WARNING = "Warning"
    WARNING_AR = "تحذير"
    CRITICAL = "Critical"
    CRITICAL_AR = "حرج"
    UNKNOWN = "Unknown"
    UNKNOWN_AR = "غير معروف"


@dataclass
class DiagnosticIssue:
    """A single diagnostic finding."""
    problem: str = ""
    evidence: str = ""
    severity: DiagnosticStatus = DiagnosticStatus.UNKNOWN
    possible_cause: str = ""
    recommended_action: str = ""


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""
    category: str = ""
    status: DiagnosticStatus = DiagnosticStatus.UNKNOWN
    issues: list[DiagnosticIssue] = field(default_factory=list)
    details: str = ""


def run_full_diagnostic() -> list[DiagnosticResult]:
    """Execute all diagnostic checks and return results."""
    results: list[DiagnosticResult] = []
    results.append(_check_cpu())
    results.append(_check_ram())
    results.append(_check_disk())
    results.append(_check_network())
    results.append(_check_security())
    results.append(_check_windows_integrity())
    results.append(_check_services())
    results.append(_check_event_logs())
    return results


def _check_cpu() -> DiagnosticResult:
    """Check CPU health."""
    result = DiagnosticResult(category="المعالج")
    if psutil is None:
        result.status = DiagnosticStatus.UNKNOWN
        result.details = "psutil غير متاح"
        return result

    cpu = cpu_service.collect_cpu_data()
    issues: list[DiagnosticIssue] = []

    if cpu.usage_percent > CPU_ALERT_THRESHOLD:
        issues.append(DiagnosticIssue(
            problem=f"استخدام المعالج مرتفع ({cpu.usage_percent:.1f}%)",
            evidence=f"الاستخدام الحالي: {cpu.usage_percent:.1f}%",
            severity=DiagnosticStatus.WARNING,
            possible_cause="عملية تستهلك موارد كبيرة أو برنامج ثقيل",
            recommended_action="تحقق من العمليات الأكثر استهلاكًا",
        ))

    if cpu.temperature is not None and cpu.temperature > 85:
        issues.append(DiagnosticIssue(
            problem=f"حرارة المعالج مرتفعة ({cpu.temperature:.0f}°C)",
            evidence=f"الحرارة: {cpu.temperature:.0f}°C",
            severity=DiagnosticStatus.CRITICAL,
            possible_cause="سوء التهوية أو تلف مبرد",
            recommended_action="تحقق من المبرد والتهوية",
        ))

    if not issues:
        result.status = DiagnosticStatus.PASSED
        result.details = f"الاستخدام: {cpu.usage_percent:.1f}% | النوى المنطقية: {cpu.logical_cores}"
    else:
        worst = max(issues, key=lambda i: [DiagnosticStatus.PASSED, DiagnosticStatus.WARNING,
                                           DiagnosticStatus.CRITICAL, DiagnosticStatus.UNKNOWN].index(i.severity))
        result.status = worst.severity

    result.issues = issues
    return result


def _check_ram() -> DiagnosticResult:
    """Check RAM health."""
    result = DiagnosticResult(category="الذاكرة")
    if psutil is None:
        result.status = DiagnosticStatus.UNKNOWN
        result.details = "psutil غير متاح"
        return result

    ram = ram_service.collect_ram_data()
    issues: list[DiagnosticIssue] = []

    if ram.usage_percent > RAM_ALERT_THRESHOLD:
        issues.append(DiagnosticIssue(
            problem=f"استخدام الذاكرة مرتفع ({ram.usage_percent:.1f}%)",
            evidence=f"المستخدم: {ram.used_gb:.1f} GB من {ram.total_gb:.1f} GB",
            severity=DiagnosticStatus.WARNING,
            possible_cause="برامج تستهلك ذاكرة كبيرة",
            recommended_action="تحقق من العمليات أو قم بترقية الذاكرة",
        ))

    if not issues:
        result.status = DiagnosticStatus.PASSED
        result.details = f"الاستخدام: {ram.usage_percent:.1f}% | المستخدم: {ram.used_gb:.1f}/{ram.total_gb:.1f} GB"
    else:
        result.status = issues[0].severity

    result.issues = issues
    return result


def _check_disk() -> DiagnosticResult:
    """Check disk health and space."""
    result = DiagnosticResult(category="الأقراص")
    if psutil is None:
        result.status = DiagnosticStatus.UNKNOWN
        return result

    disk = disk_service.collect_disk_data()
    issues: list[DiagnosticIssue] = []

    for part in disk.partitions:
        if part.usage_percent > DISK_ALERT_THRESHOLD:
            issues.append(DiagnosticIssue(
                problem=f"القرص {part.letter} ممتلئ تقريبًا ({part.usage_percent:.1f}%)",
                evidence=f"المساحة الحرة: {part.free_gb:.1f} GB",
                severity=DiagnosticStatus.CRITICAL,
                possible_cause="تراكم الملفات أو الأقراص الصغيرة",
                recommended_action="احذف ملفات غير ضرورية أو قم بتوسيع القرص",
            ))
        elif part.free_gb < DISK_SPACE_WARNING_GB:
            issues.append(DiagnosticIssue(
                problem=f"مساحة القرص {part.letter} منخفضة ({part.free_gb:.1f} GB حرة)",
                evidence=f"المساحة الحرة: {part.free_gb:.1f} GB",
                severity=DiagnosticStatus.WARNING,
                possible_cause="اقتراب القرص من الامتلاء",
                recommended_action="حرر مساحة على القرص",
            ))

    if not disk.smart_available:
        issues.append(DiagnosticIssue(
            problem="SMART غير متاح",
            evidence="تعذر قراءة بيانات SMART",
            severity=DiagnosticStatus.UNKNOWN,
            possible_cause="القرص أو النظام لا يدعم SMART",
            recommended_action="لا إجراء مطلوب – فحص SMART غير مدعوم",
        ))

    if not issues:
        result.status = DiagnosticStatus.PASSED
    else:
        worst = max(issues, key=lambda i: [DiagnosticStatus.PASSED, DiagnosticStatus.WARNING,
                                           DiagnosticStatus.CRITICAL, DiagnosticStatus.UNKNOWN].index(i.severity))
        result.status = worst.severity

    result.issues = issues
    return result


def _check_network() -> DiagnosticResult:
    """Check network connectivity."""
    result = DiagnosticResult(category="الشبكة")
    if psutil is None:
        result.status = DiagnosticStatus.UNKNOWN
        return result

    net = network_service.collect_network_data()
    connected = any(a.status == "متصل" for a in net.adapters)
    issues: list[DiagnosticIssue] = []

    if not connected:
        issues.append(DiagnosticIssue(
            problem="لا يوجد اتصال بالشبكة",
            evidence="جميع المحولات غير متصلة",
            severity=DiagnosticStatus.CRITICAL,
            possible_cause="كابل غير متصل أو شبكة Wi-Fi غير متاحة",
            recommended_action="تحقق من اتصال الشبكة",
        ))

    if net.stats.errors_in > 100 or net.stats.errors_out > 100:
        issues.append(DiagnosticIssue(
            problem="أخطاء في الشبكة",
            evidence=f"أخطاء واردة: {net.stats.errors_in} | صادرة: {net.stats.errors_out}",
            severity=DiagnosticStatus.WARNING,
            possible_cause="مشكلة في المحول أو الكابل",
            recommended_action="تحقق من المحول والكابل",
        ))

    if not issues:
        result.status = DiagnosticStatus.PASSED
    else:
        result.status = issues[0].severity

    result.issues = issues
    return result


def _check_security() -> DiagnosticResult:
    """Check security status."""
    result = DiagnosticResult(category="الأمان")
    sec = security_service.collect_security_data()
    issues: list[DiagnosticIssue] = []

    if not sec.defender_available:
        issues.append(DiagnosticIssue(
            problem="Microsoft Defender غير متاح",
            evidence="الخدمة غير موجودة",
            severity=DiagnosticStatus.UNKNOWN,
            possible_cause="مضاد فيروسات آخر مثبت أو Windows معدّل",
            recommended_action="تحقق من برنامج الحماية لديك",
        ))
    elif sec.defender_status != "قيد التشغيل":
        issues.append(DiagnosticIssue(
            problem="Microsoft Defender متوقف",
            evidence=f"الحالة: {sec.defender_status}",
            severity=DiagnosticStatus.CRITICAL,
            possible_cause="تم إيقاف الحماية يدويًا أو بواسطة برنامج آخر",
            recommended_action="أعد تفعيل الحماية الفورية",
        ))

    if sec.firewall_enabled is False:
        issues.append(DiagnosticIssue(
            problem="الجدار الناري معطّل",
            evidence=f"الحالة: {sec.firewall_status}",
            severity=DiagnosticStatus.CRITICAL,
            possible_cause="تم تعطيله يدويًا أو بواسطة برنامج",
            recommended_action="فعّل الجدار الناري فورًا",
        ))

    if not issues:
        result.status = DiagnosticStatus.PASSED
    else:
        worst = max(issues, key=lambda i: [DiagnosticStatus.PASSED, DiagnosticStatus.WARNING,
                                           DiagnosticStatus.CRITICAL, DiagnosticStatus.UNKNOWN].index(i.severity))
        result.status = worst.severity

    result.issues = issues
    return result


def _check_windows_integrity() -> DiagnosticResult:
    """Check Windows integrity (informational)."""
    result = DiagnosticResult(category="سلامة Windows")
    result.status = DiagnosticStatus.UNKNOWN
    result.details = "يتطلب تنفيذ SFC /SCANNOW – يمكن تنفيذه من صفحة الصيانة"
    return result


def _check_services() -> DiagnosticResult:
    """Check critical services status."""
    result = DiagnosticResult(category="الخدمات")
    if psutil is None:
        result.status = DiagnosticStatus.UNKNOWN
        return result

    critical_services = ["WinDefend", "EventLog", "PlugPlay", "RpcSs"]
    issues: list[DiagnosticIssue] = []

    for svc_name in critical_services:
        try:
            svc = psutil.win_service_get(svc_name)
            if svc:
                info = svc.info()
                if info.get("status") != "running":
                    issues.append(DiagnosticIssue(
                        problem=f"الخدمة {svc_name} متوقفة",
                        evidence=f"الحالة: {info.get('status', 'غير معروف')}",
                        severity=DiagnosticStatus.WARNING,
                        possible_cause="تم إيقاف الخدمة يدويًا أو بسبب خطأ",
                        recommended_action=f"أعد تشغيل الخدمة {svc_name}",
                    ))
        except Exception:
            pass

    if not issues:
        result.status = DiagnosticStatus.PASSED
    else:
        result.status = issues[0].severity

    result.issues = issues
    return result


def _check_event_logs() -> DiagnosticResult:
    """Check recent event logs for critical errors."""
    result = DiagnosticResult(category="سجل الأحداث")
    result.status = DiagnosticStatus.UNKNOWN
    result.details = "يمكن الاطلاع على سجل الأحداث من صفحة مخصصة"
    return result


def calculate_health_score(results: list[DiagnosticResult]) -> int:
    """Calculate a health score 0-100 based on diagnostic results.

    This is an ESTIMATED indicator based on available checks,
    NOT an official Windows diagnosis.
    """
    if not results:
        return 0

    score_map = {
        DiagnosticStatus.PASSED: 100,
        DiagnosticStatus.WARNING: 60,
        DiagnosticStatus.CRITICAL: 20,
        DiagnosticStatus.UNKNOWN: 70,  # neutral
    }

    scores = [score_map.get(r.status, 50) for r in results]
    return int(sum(scores) / len(scores))
