"""Report generator service.

Creates system, performance, security, maintenance, diagnostic, and full reports.
All from real collected data – never fabricates values.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.services import (
    cpu_service, ram_service, disk_service, network_service,
    gpu_service, system_service, security_service, process_service,
    service_manager, startup_service, event_log_service, system_info_service,
)
from app.diagnostics import diagnostic_service
from app.exporters.export_service import export_data


def generate_system_report(fmt: str = "json") -> Path | None:
    """Generate a comprehensive system report."""
    info = system_info_service.collect_full_info()
    data = {
        "report_type": "تقرير النظام",
        "generated_at": datetime.now().isoformat(),
        "windows": info.windows.__dict__,
        "hardware": info.hardware.__dict__,
        "driver_count": len(info.drivers),
        "drivers_sample": [d.__dict__ for d in info.drivers[:20]],
    }
    return export_data(data, "system_report", fmt, title="تقرير النظام")


def generate_performance_report(fmt: str = "json") -> Path | None:
    """Generate a performance snapshot report."""
    data = {
        "report_type": "تقرير الأداء",
        "generated_at": datetime.now().isoformat(),
        "cpu": cpu_service.collect_cpu_data().__dict__,
        "ram": ram_service.collect_ram_data().__dict__,
        "gpu": gpu_service.collect_gpu_data().__dict__,
        "disk_partitions": [p.__dict__ for p in disk_service.collect_disk_data().partitions],
        "system": system_service.collect_system_data().__dict__,
    }
    return export_data(data, "performance_report", fmt, title="تقرير الأداء")


def generate_security_report(fmt: str = "json") -> Path | None:
    """Generate a security status report."""
    sec = security_service.collect_security_data()
    data = {
        "report_type": "تقرير الأمان",
        "generated_at": datetime.now().isoformat(),
        "security": sec.__dict__,
    }
    return export_data(data, "security_report", fmt, title="تقرير الأمان")


def generate_maintenance_report(fmt: str = "json") -> Path | None:
    """Generate a maintenance log report."""
    log_path = Path("logs/operations.log")
    ops: list[str] = []
    if log_path.exists():
        ops = log_path.read_text(encoding="utf-8").splitlines()[-100:]
    data = {
        "report_type": "تقرير الصيانة",
        "generated_at": datetime.now().isoformat(),
        "recent_operations": ops,
    }
    return export_data(data, "maintenance_report", fmt, title="تقرير الصيانة")


def generate_diagnostic_report(fmt: str = "json") -> Path | None:
    """Generate a diagnostic report."""
    results = diagnostic_service.run_full_diagnostic()
    health = diagnostic_service.calculate_health_score(results)
    data = {
        "report_type": "تقرير التشخيص",
        "generated_at": datetime.now().isoformat(),
        "health_score": health,
        "health_score_note": "مؤشر تقديري مبني على الفحوصات المتاحة وليس تشخيصًا رسميًا من Windows",
        "checks": [
            {
                "category": r.category,
                "status": r.status.value if hasattr(r.status, "value") else str(r.status),
                "details": r.details,
                "issues": [i.__dict__ for i in r.issues],
            }
            for r in results
        ],
    }
    return export_data(data, "diagnostic_report", fmt, title="تقرير التشخيص")


def generate_full_report(fmt: str = "json") -> Path | None:
    """Generate a full combined report."""
    info = system_info_service.collect_full_info()
    cpu = cpu_service.collect_cpu_data()
    ram = ram_service.collect_ram_data()
    disk = disk_service.collect_disk_data()
    net = network_service.collect_network_data()
    gpu = gpu_service.collect_gpu_data()
    sys = system_service.collect_system_data()
    sec = security_service.collect_security_data()
    diag = diagnostic_service.run_full_diagnostic()
    health = diagnostic_service.calculate_health_score(diag)

    data = {
        "report_type": "التقرير الشامل",
        "generated_at": datetime.now().isoformat(),
        "health_score": health,
        "health_score_note": "مؤشر تقديري مبني على الفحوصات المتاحة وليس تشخيصًا رسميًا من Windows",
        "system_info": info.windows.__dict__,
        "hardware": info.hardware.__dict__,
        "cpu": cpu.__dict__,
        "ram": ram.__dict__,
        "disk": {"partitions": [p.__dict__ for p in disk.partitions]},
        "network": {
            "adapters": [a.__dict__ for a in net.adapters],
            "stats": net.stats.__dict__,
        },
        "gpu": gpu.__dict__,
        "system": sys.__dict__,
        "security": sec.__dict__,
        "diagnostics": [
            {"category": r.category, "status": str(r.status)}
            for r in diag
        ],
    }
    return export_data(data, "full_report", fmt, title="التقرير الشامل")
