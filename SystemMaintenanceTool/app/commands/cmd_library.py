"""Command Library for CMD Center.

Each command has real metadata: name, description, syntax, example,
risk level, and category.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CommandEntry:
    """A single command definition."""
    name: str
    name_ar: str
    description: str
    syntax: str
    example: str
    risk: str  # safe / caution / dangerous
    category: str  # system / network / disk / process / security / services / repair / advanced
    shell: str  # cmd / powershell / both
    requires_admin: bool = False


COMMANDS: list[CommandEntry] = [
    # ── System ─────────────────────────────────────────────────────
    CommandEntry(
        name="systeminfo", name_ar="معلومات النظام",
        description="عرض معلومات مفصلة عن النظام والعتاد",
        syntax="systeminfo",
        example="systeminfo",
        risk="safe", category="system", shell="cmd",
    ),
    CommandEntry(
        name="hostname", name_ar="اسم الجهاز",
        description="عرض اسم الجهاز الحالي",
        syntax="hostname",
        example="hostname",
        risk="safe", category="system", shell="cmd",
    ),
    CommandEntry(
        name="whoami", name_ar="المستخدم الحالي",
        description="عرض اسم المستخدم الحالي",
        syntax="whoami",
        example="whoami",
        risk="safe", category="system", shell="cmd",
    ),
    CommandEntry(
        name="tasklist", name_ar="قائمة العمليات",
        description="عرض جميع العمليات الجارية",
        syntax="tasklist",
        example="tasklist /v",
        risk="safe", category="process", shell="cmd",
    ),
    CommandEntry(
        name="taskkill", name_ar="إنهاء عملية",
        description="إنهاء عملية بالمعرف أو الاسم",
        syntax="taskkill /PID <pid> /F",
        example="taskkill /PID 1234 /F",
        risk="caution", category="process", shell="cmd", requires_admin=False,
    ),
    # ── Network ────────────────────────────────────────────────────
    CommandEntry(
        name="ipconfig", name_ar="إعدادات الشبكة",
        description="عرض إعدادات الشبكة",
        syntax="ipconfig /all",
        example="ipconfig /all",
        risk="safe", category="network", shell="cmd",
    ),
    CommandEntry(
        name="ping", name_ar="اختبار الاتصال",
        description="اختبار الاتصال بمضيف",
        syntax="ping <host>",
        example="ping 8.8.8.8",
        risk="safe", category="network", shell="cmd",
    ),
    CommandEntry(
        name="tracert", name_ar="تتبع المسار",
        description="تتبع مسار الحزم إلى مضيف",
        syntax="tracert <host>",
        example="tracert google.com",
        risk="safe", category="network", shell="cmd",
    ),
    CommandEntry(
        name="netstat", name_ar="اتصالات الشبكة",
        description="عرض اتصالات الشبكة والمنافذ",
        syntax="netstat -ano",
        example="netstat -ano",
        risk="safe", category="network", shell="cmd",
    ),
    CommandEntry(
        name="nslookup", name_ar="استعلام DNS",
        description="استعلام عن اسم نطاق",
        syntax="nslookup <domain>",
        example="nslookup google.com",
        risk="safe", category="network", shell="cmd",
    ),
    CommandEntry(
        name="arp", name_ar="جدول ARP",
        description="عرض جدول ARP",
        syntax="arp -a",
        example="arp -a",
        risk="safe", category="network", shell="cmd",
    ),
    # ── Disk ────────────────────────────────────────────────────────
    CommandEntry(
        name="chkdsk", name_ar="فحص القرص",
        description="فحص وإصلاح القرص",
        syntax="chkdsk <drive>: /f",
        example="chkdsk C: /f",
        risk="caution", category="disk", shell="cmd", requires_admin=True,
    ),
    CommandEntry(
        name="diskpart", name_ar="إدارة الأقراص",
        description="أداة إدارة الأقراص المتقدمة",
        syntax="diskpart",
        example="diskpart",
        risk="dangerous", category="disk", shell="cmd", requires_admin=True,
    ),
    # ── Security ────────────────────────────────────────────────────
    CommandEntry(
        name="Get-MpComputerStatus", name_ar="حالة Defender",
        description="عرض حالة Microsoft Defender",
        syntax="Get-MpComputerStatus",
        example="Get-MpComputerStatus",
        risk="safe", category="security", shell="powershell", requires_admin=True,
    ),
    CommandEntry(
        name="Get-NetFirewallProfile", name_ar="حالة الجدار الناري",
        description="عرض حالة الجدار الناري",
        syntax="Get-NetFirewallProfile",
        example="Get-NetFirewallProfile",
        risk="safe", category="security", shell="powershell", requires_admin=True,
    ),
    # ── Services ────────────────────────────────────────────────────
    CommandEntry(
        name="sc query", name_ar="حالة الخدمات",
        description="عرض حالة جميع خدمات Windows",
        syntax="sc query state= all",
        example="sc query state= all",
        risk="safe", category="services", shell="cmd",
    ),
    CommandEntry(
        name="sc config", name_ar="تغيير نوع بدء الخدمة",
        description="تغيير نوع بدء تشغيل خدمة",
        syntax="sc config <service> start= <type>",
        example="sc config WinDefend start= auto",
        risk="caution", category="services", shell="cmd", requires_admin=True,
    ),
    # ── Repair ──────────────────────────────────────────────────────
    CommandEntry(
        name="sfc", name_ar="فحص ملفات النظام",
        description="فحص وإصلاح ملفات النظام",
        syntax="sfc /scannow",
        example="sfc /scannow",
        risk="caution", category="repair", shell="cmd", requires_admin=True,
    ),
    CommandEntry(
        name="dism", name_ar="صيانة صورة Windows",
        description="فحص وإصلاح صورة Windows",
        syntax="dism /online /cleanup-image /restorehealth",
        example="dism /online /cleanup-image /restorehealth",
        risk="caution", category="repair", shell="cmd", requires_admin=True,
    ),
    # ── Advanced ────────────────────────────────────────────────────
    CommandEntry(
        name="wmic", name_ar="WMI Commands",
        description="أوامر إدارة Windows",
        syntax="wmic <class> get <properties>",
        example="wmic cpu get name,numberOfCores",
        risk="safe", category="advanced", shell="cmd",
    ),
    CommandEntry(
        name="powershell", name_ar="PowerShell",
        description="تنفيذ أوامر PowerShell",
        syntax="powershell -Command \"<cmd>\"",
        example='powershell -Command "Get-Process | Select-Object -First 10"',
        risk="caution", category="advanced", shell="powershell",
    ),
    CommandEntry(
        name="reg", name_ar="محرر التسجيل",
        description="الاستعلام عن مفاتيح التسجيل",
        syntax="reg query <key>",
        example='reg query "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion"',
        risk="dangerous", category="advanced", shell="cmd", requires_admin=True,
    ),
]


def get_commands_by_category(category: str) -> list[CommandEntry]:
    """Filter commands by category."""
    return [c for c in COMMANDS if c.category == category]


def search_commands(query: str) -> list[CommandEntry]:
    """Search commands by name or description."""
    q = query.lower()
    return [
        c for c in COMMANDS
        if q in c.name.lower() or q in c.name_ar or q in c.description
    ]
