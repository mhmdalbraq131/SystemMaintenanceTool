"""Lightweight native Windows UI for System Maintenance Tool."""
from __future__ import annotations

import ctypes
import json
import os
import platform
import socket
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import psutil

try:
    import wmi  # type: ignore
except Exception:
    wmi = None

BG = "#030712"
PANEL = "#07111f"
PANEL2 = "#0d1b2e"
TEXT = "#dff7ff"
MUTED = "#66809c"
ACCENT = "#00d9ff"
ACCENT2 = "#7c3aed"
GOOD = "#00f5a0"
WARN = "#ffb020"
DANGER = "#ff4d6d"


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def run_native(command: list[str], timeout: int = 900) -> tuple[int, str]:
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    p = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=flags,
    )
    return p.returncode, ((p.stdout or "") + "\n" + (p.stderr or "")).strip()


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SYSTEM MAINTENANCE // COMMAND DECK")
        self.geometry("1320x820")
        self.minsize(1100, 700)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self._build_style()
        self._build_layout()
        self.show("dashboard")
        self.after(500, self.refresh_dashboard)
        self.after(3500, self._live_refresh)

    def _setup_icon(self) -> None:
        try:
            self.iconbitmap(default="")
        except Exception:
            pass

    def _button(self, parent, text, command, primary=False):
        return tk.Button(
            parent, text=text, command=command,
            bg=ACCENT if primary else PANEL2,
            fg="white" if primary else TEXT,
            activebackground="#3b82f6",
            activeforeground="white",
            relief="flat", bd=0,
            padx=18, pady=9,
            font=("Segoe UI", 10, "bold" if primary else "normal"),
            cursor="hand2"
        )

    def _metric_ring(self, parent, title, value, subtitle, col):
        box = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=PANEL2)
        box.grid(row=0, column=col, sticky="nsew", padx=6, pady=6)
        tk.Label(box, text=title, bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 10, "bold"), anchor="e").pack(fill="x", padx=16, pady=(14, 0))
        row = tk.Frame(box, bg=PANEL)
        row.pack(fill="x", padx=16, pady=4)
        v = tk.Label(row, text=value, bg=PANEL, fg="white",
                     font=("Segoe UI", 28, "bold"), anchor="e")
        v.pack(side="right")
        tk.Label(row, text=subtitle, bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9), anchor="e").pack(side="right", padx=(0, 10))
        bar = ttk.Progressbar(box, mode="determinate", maximum=100)
        bar.pack(fill="x", padx=16, pady=(4, 16))
        return v, bar

    def _build_style(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                    foreground=TEXT, rowheight=28, borderwidth=0)
        s.configure("Treeview.Heading", background=PANEL2, foreground=TEXT,
                    relief="flat", font=("Segoe UI", 9, "bold"))
        s.configure("TProgressbar", troughcolor=PANEL2, background=ACCENT,
                    borderwidth=0)

    def _build_layout(self) -> None:
        head = tk.Frame(self, bg="#0b1220", height=66)
        head.pack(fill="x")
        tk.Label(head, text="◈ SYSTEM MAINTENANCE", bg="#040a14", fg=ACCENT,
                 font=("Consolas", 18, "bold")).pack(side="right", padx=24, pady=15)
        tk.Label(head, text="COMMAND DECK  //  WINDOWS", bg="#040a14", fg=MUTED,
                 font=("Consolas", 9)).pack(side="right", padx=2, pady=19)
        self.status = tk.Label(head, text="SYSTEM READY", bg="#040a14", fg=ACCENT,
                               font=("Consolas", 9, "bold"))
        self.status.pack(side="left", padx=24)
        tk.Label(head, text="● SYSTEM LINK ONLINE", bg="#040a14", fg=GOOD,
                 font=("Consolas", 9, "bold")).pack(side="left", padx=10)

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        nav = tk.Frame(body, bg=PANEL, width=225)
        nav.pack(side="right", fill="y")
        nav.pack_propagate(False)
        tk.Label(nav, text="◈ FLIGHT SYSTEMS", bg=PANEL, fg=ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(fill="x", padx=18, pady=(22, 4))
        tk.Label(nav, text="مركز قيادة وصيانة النظام", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9)).pack(fill="x", padx=18, pady=(0, 12))
        tk.Frame(nav, bg=ACCENT, height=1).pack(fill="x", padx=18, pady=(0, 10))

        items = [
            ("dashboard", "⌂  لوحة المعلومات"),
            ("system", "▣  معلومات النظام"),
            ("processes", "◉  العمليات"),
            ("storage", "▤  التخزين"),
            ("network", "⌁  الشبكة"),
            ("security", "◆  الأمان"),
            ("maintenance", "⚙  الصيانة والإصلاح"),
            ("services", "▤  خدمات Windows"),
            ("startup", "↗  بدء التشغيل"),
            ("commands", "⌘  محطة الأوامر"),
            ("reports", "▥  التقارير"),
        ]
        self.buttons: dict[str, tk.Button] = {}
        for key, title in items:
            b = tk.Button(nav, text=title, command=lambda k=key: self.show(k),
                          bg=PANEL, fg=TEXT, activebackground="#12384a",
                          activeforeground="white", relief="flat", bd=0,
                          anchor="e", padx=18, pady=9,
                          font=("Segoe UI", 10), cursor="hand2")
            b.pack(fill="x", padx=8, pady=1)
            self.buttons[key] = b

        self.content = tk.Frame(body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        self.pages: dict[str, tk.Frame] = {}
        for key, title in items:
            self.page(key, title)

        self._dashboard_controls()
        self._system_controls()
        self._process_controls()
        self._storage_controls()
        self._network_controls()
        self._security_controls()
        self._maintenance_controls()
        self._service_controls()
        self._startup_controls()
        self._command_controls()
        self._report_controls()

    def page(self, key: str, title: str) -> tk.Frame:
        frame = tk.Frame(self.content, bg=BG)
        self.pages[key] = frame
        if key != "dashboard":
            titlebar = tk.Frame(frame, bg=BG)
            titlebar.pack(fill="x", padx=24, pady=(20, 12))
            tk.Label(titlebar, text=title, bg=BG, fg=TEXT,
                     font=("Segoe UI", 20, "bold"), anchor="e").pack(side="right")
            tk.Label(titlebar, text=f"// {key.upper()}", bg=BG, fg=MUTED,
                     font=("Consolas", 9)).pack(side="left", pady=8)
            tk.Frame(frame, bg="#16364a", height=1).pack(fill="x", padx=24, pady=(0, 10))
        return frame

    def show(self, key: str) -> None:
        for frame in self.pages.values():
            frame.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        for k, button in self.buttons.items():
            button.configure(bg="#12384a" if k == key else PANEL, fg=ACCENT if k == key else TEXT)
        self.status.configure(text=self.buttons[key].cget("text"))

    def card(self, parent: tk.Frame, title: str, col: int, row: int) -> tk.Label:
        """Create a card using a dedicated internal grid container.

        The parent page is intentionally kept pack-managed for its header;
        the dashboard body uses one dedicated grid container so Tkinter never
        mixes geometry managers inside the same master.
        """
        container = getattr(parent, "_cards_container", None)
        if container is None:
            container = tk.Frame(parent, bg=BG)
            container.pack(fill="x", padx=6, pady=6)
            for index in range(3):
                container.grid_columnconfigure(index, weight=1, uniform="card")
            parent._cards_container = container  # type: ignore[attr-defined]

        card = tk.Frame(container, bg=PANEL, highlightthickness=1,
                        highlightbackground=PANEL2)
        card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
        tk.Label(card, text=title, bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 10), anchor="e").pack(
                 fill="x", padx=14, pady=(12, 2))
        value = tk.Label(card, text="—", bg=PANEL, fg=TEXT,
                         font=("Consolas", 20, "bold"), anchor="e")
        value.pack(fill="x", padx=14, pady=(0, 12))
        return value

    def _dashboard_controls(self) -> None:
        f = self.pages["dashboard"]

        # --- Command-deck hero -------------------------------------------------
        hero = tk.Frame(f, bg=PANEL, highlightthickness=1, highlightbackground="#12304a")
        hero.pack(fill="x", padx=24, pady=(0, 12))

        left = tk.Frame(hero, bg=PANEL)
        left.pack(side="left", fill="y", padx=22, pady=18)
        tk.Label(left, text="● LIVE MONITORING", bg=PANEL, fg=GOOD,
                 font=("Consolas", 9, "bold")).pack(anchor="w")
        self.health = tk.Label(left, text="SYSTEM NOMINAL",
                               bg=PANEL, fg=TEXT, font=("Segoe UI", 11, "bold"))
        self.health.pack(anchor="w", pady=(8, 0))

        right = tk.Frame(hero, bg=PANEL)
        right.pack(side="right", fill="both", expand=True, padx=24, pady=15)
        tk.Label(right, text="لوحة القيادة", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 24, "bold"), anchor="e").pack(fill="x")
        tk.Label(right, text="مراقبة النظام والتحكم والصيانة في مكان واحد",
                 bg=PANEL, fg=MUTED, font=("Segoe UI", 10), anchor="e").pack(fill="x", pady=(2, 0))

        # --- Live telemetry ----------------------------------------------------
        telemetry = tk.Frame(f, bg=BG)
        telemetry.pack(fill="x", padx=18, pady=2)
        for col in range(3):
            telemetry.grid_columnconfigure(col, weight=1, uniform="telemetry")

        self.metric_bars = {}
        self.metric_values = {}
        specs = [
            ("المعالج", "CPU", "dc", 0, ACCENT),
            ("الذاكرة", "RAM", "dr", 1, ACCENT2),
            ("التخزين", "DISK", "dd", 2, WARN),
        ]
        for title, code, attr, col, accent in specs:
            box = tk.Frame(telemetry, bg=PANEL, highlightthickness=1,
                           highlightbackground="#13263b")
            box.grid(row=0, column=col, sticky="nsew", padx=6, pady=6)
            top = tk.Frame(box, bg=PANEL)
            top.pack(fill="x", padx=16, pady=(14, 4))
            tk.Label(top, text=code, bg=PANEL, fg=accent,
                     font=("Consolas", 9, "bold")).pack(side="left")
            tk.Label(top, text=title, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 10, "bold")).pack(side="right")
            value = tk.Label(box, text="0%", bg=PANEL, fg=TEXT,
                             font=("Consolas", 25, "bold"), anchor="e")
            value.pack(fill="x", padx=16)
            bar = ttk.Progressbar(box, maximum=100, mode="determinate")
            bar.pack(fill="x", padx=16, pady=(7, 16))
            setattr(self, attr, value)
            self.metric_values[attr] = value
            self.metric_bars[attr] = bar

        # --- Secondary telemetry ----------------------------------------------
        info = tk.Frame(f, bg=BG)
        info.pack(fill="x", padx=18, pady=2)
        for col in range(3):
            info.grid_columnconfigure(col, weight=1, uniform="info")

        secondary = [
            ("العمليات", "PROCESSES", "dp", 0),
            ("مدة التشغيل", "UPTIME", "du", 1),
            ("صلاحيات المسؤول", "PRIVILEGES", "da", 2),
        ]
        for title, code, attr, col in secondary:
            box = tk.Frame(info, bg="#091522", highlightthickness=1,
                           highlightbackground="#13263b")
            box.grid(row=0, column=col, sticky="nsew", padx=6, pady=6)
            tk.Label(box, text=code, bg="#091522", fg=MUTED,
                     font=("Consolas", 8, "bold")).pack(anchor="e", padx=14, pady=(10, 0))
            value = tk.Label(box, text="—", bg="#091522", fg=TEXT,
                             font=("Segoe UI", 14, "bold"), anchor="e")
            value.pack(fill="x", padx=14, pady=(2, 12))
            setattr(self, attr, value)

        # --- Quick launch ------------------------------------------------------
        launch = tk.Frame(f, bg=PANEL, highlightthickness=1, highlightbackground="#13263b")
        launch.pack(fill="x", padx=24, pady=(12, 0))
        tk.Label(launch, text="QUICK LAUNCH", bg=PANEL, fg=ACCENT,
                 font=("Consolas", 9, "bold")).pack(anchor="e", padx=18, pady=(12, 4))
        row = tk.Frame(launch, bg=PANEL)
        row.pack(fill="x", padx=12, pady=(2, 14))
        actions = [
            ("فحص النظام", self.health_check, True),
            ("تنظيف المؤقتات", self.clean_temp, False),
            ("فحص SFC", lambda: self.command(["sfc", "/scannow"]), False),
            ("تفريغ DNS", lambda: self.command(["ipconfig", "/flushdns"]), False),
            ("محطة الأوامر", lambda: self.show("commands"), False),
        ]
        for title, fn, primary in actions:
            self._button(row, title, fn, primary).pack(side="right", padx=4)

        # Keep the lower health panel compact and informative.
        detail = tk.Frame(f, bg="#091522", highlightthickness=1, highlightbackground="#13263b")
        detail.pack(fill="x", padx=24, pady=10)
        tk.Label(detail, text="SYSTEM DIAGNOSTICS", bg="#091522", fg=MUTED,
                 font=("Consolas", 8, "bold")).pack(anchor="e", padx=16, pady=(10, 0))
        self.health_detail = tk.Label(detail, text="جاري قراءة مؤشرات النظام...",
                                      bg="#091522", fg=TEXT,
                                      font=("Segoe UI", 10), anchor="e")
        self.health_detail.pack(fill="x", padx=16, pady=(3, 12))

    def _system_controls(self) -> None:
        f = self.pages["system"]
        self.system = self.textbox(f)
        tk.Button(f, text="تحديث", command=self.refresh_system,
                  bg=ACCENT, fg="white", relief="flat", padx=18, pady=8).pack(
                  anchor="e", padx=24, pady=5)

    def _process_controls(self) -> None:
        f = self.pages["processes"]
        self.proc = self.tree(f, ("pid", "name", "cpu", "ram"),
                              ("PID", "العملية", "CPU %", "RAM %"))
        tk.Button(f, text="تحديث العمليات", command=self.refresh_processes,
                  bg=ACCENT, fg="white", relief="flat", padx=18, pady=8).pack(
                  anchor="e", padx=24, pady=5)

    def _storage_controls(self) -> None:
        f = self.pages["storage"]
        self.storage = self.textbox(f)
        tk.Button(f, text="فحص الأقراص", command=self.refresh_storage,
                  bg=ACCENT, fg="white", relief="flat", padx=18, pady=8).pack(
                  anchor="e", padx=24, pady=5)

    def _network_controls(self) -> None:
        f = self.pages["network"]
        self.network = self.textbox(f)
        tk.Button(f, text="فحص الشبكة", command=self.refresh_network,
                  bg=ACCENT, fg="white", relief="flat", padx=18, pady=8).pack(
                  anchor="e", padx=24, pady=5)

    def _security_controls(self) -> None:
        f = self.pages["security"]
        self.security = self.textbox(f)
        tk.Button(f, text="فحص الأمان", command=self.refresh_security,
                  bg=ACCENT, fg="white", relief="flat", padx=18, pady=8).pack(
                  anchor="e", padx=24, pady=5)

    def _maintenance_controls(self) -> None:
        f = self.pages["maintenance"]
        actions = [
            ("تنظيف الملفات المؤقتة", self.clean_temp),
            ("فحص ملفات Windows — SFC", lambda: self.command(["sfc", "/scannow"])),
            ("إصلاح Windows — DISM", lambda: self.command(
                ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"])),
            ("فحص القرص — CHKDSK", lambda: self.command(["chkdsk", "C:", "/scan"])),
            ("تفريغ DNS", lambda: self.command(["ipconfig", "/flushdns"])),
            ("إعادة ضبط Winsock", lambda: self.command(["netsh", "winsock", "reset"])),
        ]
        for title, fn in actions:
            tk.Button(f, text=title, command=fn, bg=PANEL2, fg=TEXT,
                      activebackground=ACCENT, activeforeground="white",
                      relief="flat", anchor="e", padx=18, pady=11,
                      font=("Segoe UI", 10)).pack(fill="x", padx=24, pady=4)
        tk.Label(f,
                 text=("تشغيل كمسؤول: نعم" if is_admin()
                       else "تنبيه: شغّل الأداة كمسؤول لتنفيذ إصلاحات Windows."),
                 bg=BG, fg=("#86efac" if is_admin() else WARN),
                 font=("Segoe UI", 10)).pack(anchor="e", padx=24, pady=10)

    def _service_controls(self) -> None:
        f = self.pages["services"]
        self.services = self.textbox(f, ("Consolas", 9))
        tk.Button(f, text="عرض الخدمات", command=self.refresh_services,
                  bg=ACCENT, fg="white", relief="flat", padx=18, pady=8).pack(
                  anchor="e", padx=24, pady=5)

    def _startup_controls(self) -> None:
        f = self.pages["startup"]
        self.startup = self.textbox(f, ("Consolas", 9))
        tk.Button(f, text="فحص بدء التشغيل", command=self.refresh_startup,
                  bg=ACCENT, fg="white", relief="flat", padx=18, pady=8).pack(
                  anchor="e", padx=24, pady=5)

    def _command_controls(self) -> None:
        f = self.pages["commands"]
        top = tk.Frame(f, bg=PANEL, highlightthickness=1, highlightbackground=PANEL2)
        top.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(top, text="⌘  COMMAND TERMINAL", bg=PANEL, fg=ACCENT,
                 font=("Consolas", 12, "bold")).pack(side="left", padx=16, pady=12)
        tk.Label(top, text="محطة أوامر Windows المدمجة", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9)).pack(side="right", padx=16, pady=12)

        quick = tk.Frame(f, bg=BG)
        quick.pack(fill="x", padx=24, pady=4)
        for label, cmd in [("SYSTEMINFO", "systeminfo"), ("IPCONFIG", "ipconfig"),
                           ("TASKLIST", "tasklist"), ("SERVICES", "sc query"),
                           ("WHOAMI", "whoami")]:
            self._button(quick, label, lambda value=cmd: self._set_command(value)).pack(
                side="right", padx=3)

        row = tk.Frame(f, bg=BG)
        row.pack(fill="x", padx=24, pady=6)
        self.cmd_entry = tk.Entry(row, bg="#020812", fg=ACCENT, insertbackground=ACCENT,
                                  relief="flat", font=("Consolas", 12))
        self.cmd_entry.pack(side="right", fill="x", expand=True, ipady=10, padx=(0, 8))
        self._button(row, "EXECUTE  ▶", self.run_custom_command, True).pack(side="right")

        self.cmd_output = tk.Text(f, bg="#02050a", fg="#9be7ff", insertbackground=ACCENT,
                                  relief="flat", wrap="none", font=("Consolas", 10))
        self.cmd_output.pack(fill="both", expand=True, padx=24, pady=8)
        self.cmd_output.insert("end",
            "SYSTEM MAINTENANCE TERMINAL\n"
            "════════════════════════════════════════════════════════════\n"
            "LINK: ONLINE    SHELL: CMD.EXE    MODE: ADMIN-AWARE\n\n"
            "PS> ")
        self.cmd_output.configure(state="disabled")

    def _button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command,
                         bg="#0c4050" if primary else PANEL2,
                         fg=ACCENT if primary else TEXT,
                         activebackground="#155e75", activeforeground="white",
                         relief="flat", bd=0, padx=16, pady=9,
                         font=("Consolas", 9, "bold"), cursor="hand2")

    def _set_command(self, value: str) -> None:
        self.cmd_entry.delete(0, "end")
        self.cmd_entry.insert(0, value)
        self.cmd_entry.focus_set()

    def _report_controls(self) -> None:
        f = self.pages["reports"]
        self.report = self.textbox(f, ("Consolas", 9))
        bar = tk.Frame(f, bg=BG)
        bar.pack(fill="x", padx=24, pady=5)
        tk.Button(bar, text="توليد التقرير", command=self.refresh_report,
                  bg=ACCENT, fg="white", relief="flat", padx=18, pady=8).pack(side="right")
        tk.Button(bar, text="حفظ TXT", command=self.save_txt,
                  bg=PANEL2, fg=TEXT, relief="flat", padx=18, pady=8).pack(side="right", padx=5)
        tk.Button(bar, text="حفظ JSON", command=self.save_json,
                  bg=PANEL2, fg=TEXT, relief="flat", padx=18, pady=8).pack(side="right")

    def textbox(self, parent: tk.Misc, font=("Segoe UI", 10)) -> tk.Text:
        text = tk.Text(parent, bg=PANEL, fg=TEXT, insertbackground="white",
                       relief="flat", wrap="word", font=font)
        text.pack(fill="both", expand=True, padx=24, pady=6)
        return text

    def tree(self, parent: tk.Misc, cols: tuple[str, ...], heads: tuple[str, ...]) -> ttk.Treeview:
        wrapper = tk.Frame(parent, bg=BG)
        wrapper.pack(fill="both", expand=True, padx=24, pady=6)
        tree = ttk.Treeview(wrapper, columns=cols, show="headings")
        for col, head in zip(cols, heads):
            tree.heading(col, text=head)
            tree.column(col, anchor="center", width=150)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(wrapper, orient="vertical", command=tree.yview)
        scrollbar.pack(side="right", fill="y")
        tree.configure(yscrollcommand=scrollbar.set)
        return tree

    def _live_refresh(self) -> None:
        self.refresh_dashboard()
        self.after(3500, self._live_refresh)

    def refresh_dashboard(self) -> None:
        try:
            cpu = psutil.cpu_percent(None)
            ram = psutil.virtual_memory().percent
            disk = max((psutil.disk_usage(p.mountpoint).percent
                        for p in psutil.disk_partitions(all=False)
                        if os.path.exists(p.mountpoint)), default=0)
                self.dc.config(text=f"{cpu:.0f}%")
            self.dr.config(text=f"{ram:.0f}%")
            self.dd.config(text=f"{disk:.0f}%")
            self.metric_bars["dc"]["value"] = cpu
            self.metric_bars["dr"]["value"] = ram
            self.metric_bars["dd"]["value"] = disk
            self.dp.config(text=str(len(psutil.pids())))
            self.du.config(text=self.uptime())
            self.da.config(text="نعم" if is_admin() else "لا")
            worst = max(cpu, ram, disk)
            self.health.config(text=("● CRITICAL / حالة حرجة" if worst >= 90 else
                                     "● ATTENTION / تحتاج انتباه" if worst >= 75 else
                                     "● SYSTEM NOMINAL / النظام مستقر"))
            self.health_detail.config(
                text=f"CPU {cpu:.0f}%   •   RAM {ram:.0f}%   •   DISK {disk:.0f}%   •   PROCESSES {len(psutil.pids())}")
        except Exception as exc:
            self.status.config(text=f"خطأ: {exc}")

    def refresh_system(self) -> None:
        lines = [
            f"اسم الجهاز: {socket.gethostname()}",
            f"النظام: {platform.platform()}",
            f"إصدار Windows: {platform.version()}",
            f"المعمارية: {platform.machine()}",
            f"Python: {platform.python_version()}",
            f"المعالج: {psutil.cpu_count(logical=False) or 0} أنوية فعلية / {psutil.cpu_count() or 0} منطقية",
            f"الذاكرة: {psutil.virtual_memory().total / 1024**3:.2f} GB",
            f"الإقلاع: {datetime.fromtimestamp(psutil.boot_time()):%Y-%m-%d %H:%M:%S}",
            f"صلاحيات المسؤول: {'نعم' if is_admin() else 'لا'}",
        ]
        self.replace(self.system, "\n".join(lines))

    def refresh_processes(self) -> None:
        for item in self.proc.get_children():
            self.proc.delete(item)
        rows = []
        for process in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                rows.append((process.info["pid"], process.info["name"] or "",
                             process.info["cpu_percent"] or 0,
                             process.info["memory_percent"] or 0))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        for row in sorted(rows, key=lambda x: x[2], reverse=True)[:150]:
            self.proc.insert("", "end", values=(row[0], row[1], f"{row[2]:.1f}", f"{row[3]:.1f}"))

    def refresh_storage(self) -> None:
        out = []
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                out.append(f"{p.device}  {usage.total/1024**3:.1f} GB | "
                           f"متاح {usage.free/1024**3:.1f} GB | مستخدم {usage.percent:.1f}%")
            except OSError:
                pass
        self.replace(self.storage, "\n".join(out) or "لم يتم العثور على أقراص.")

    def refresh_network(self) -> None:
        counters = psutil.net_io_counters()
        lines = [f"إرسال: {counters.bytes_sent/1024**2:.1f} MB",
                 f"استقبال: {counters.bytes_recv/1024**2:.1f} MB", ""]
        for name, addrs in psutil.net_if_addrs().items():
            lines.append(name + ":")
            lines.extend("  " + addr.address for addr in addrs)
        self.replace(self.network, "\n".join(lines))

    def refresh_security(self) -> None:
        lines = [f"صلاحيات المسؤول: {'نعم' if is_admin() else 'لا'}"]
        if wmi:
            try:
                c = wmi.WMI()
                for antivirus in c.query("SELECT displayName, productState FROM AntiVirusProduct"):
                    lines.append(f"مكافح الفيروسات: {antivirus.displayName} | الحالة: {antivirus.productState}")
            except Exception as exc:
                lines.append(f"تعذر قراءة WMI للأمان: {exc}")
        else:
            lines.append("WMI غير متاح؛ تم استخدام الموارد الأساسية فقط.")
        self.replace(self.security, "\n".join(lines))

    def refresh_services(self) -> None:
        self._async_command(["sc", "query", "type=", "service", "state=", "all"], self.services, 20)

    def refresh_startup(self) -> None:
        self._async_command(["reg", "query",
                             r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"],
                            self.startup, 15)

    def command(self, cmd: list[str]) -> None:
        if not messagebox.askyesno("تأكيد", "سيتم تنفيذ عملية صيانة في Windows. المتابعة?"):
            return
        self.status.config(text="جاري تنفيذ العملية...")
        self._async_command(cmd, None, 900, show_window=True)

    def run_custom_command(self) -> None:
        raw = self.cmd_entry.get().strip()
        if not raw:
            return
        if not messagebox.askyesno("تأكيد", "تنفيذ الأمر كما كُتب؟"):
            return
        self._async_custom(raw)

    def _async_custom(self, raw: str) -> None:
        self._console_write("\nPS> " + raw + "\n")
        def worker() -> None:
            try:
                code, output = run_native(["cmd", "/c", raw], 900)
                self.after(0, lambda: self._console_write(
                    f"{output}\n\n[EXIT {code}]\nPS> "))
            except Exception as exc:
                self.after(0, lambda: self._console_write(f"ERROR: {exc}\nPS> "))
        threading.Thread(target=worker, daemon=True).start()

    def _console_write(self, text: str) -> None:
        self.cmd_output.configure(state="normal")
        self.cmd_output.insert("end", text)
        self.cmd_output.see("end")
        self.cmd_output.configure(state="disabled")

    def _async_command(self, cmd: list[str], target: tk.Text | None,
                       timeout: int, show_window: bool = False) -> None:
        def worker() -> None:
            try:
                code, output = run_native(cmd, timeout)
                text = f"Exit code: {code}\n\n{output}"
                self.after(0, lambda: self._command_done(target, text, show_window))
            except Exception as exc:
                self.after(0, lambda: self._command_done(target, str(exc), show_window))
        threading.Thread(target=worker, daemon=True).start()

    def _command_done(self, target: tk.Text | None, text: str, show_window: bool) -> None:
        self.status.config(text="اكتملت العملية")
        if target is not None:
            self.replace(target, text)
        elif show_window:
            win = tk.Toplevel(self)
            win.title("نتيجة العملية")
            win.geometry("900x560")
            output = self.textbox(win, font=("Consolas", 9))
            self.replace(output, text)

    def health_check(self) -> None:
        self.status.config(text="جاري فحص الصحة...")

        def worker() -> None:
            try:
                cpu = psutil.cpu_percent(interval=1)
                ram = psutil.virtual_memory().percent
                disk = max((psutil.disk_usage(p.mountpoint).percent
                            for p in psutil.disk_partitions(all=False)
                            if os.path.exists(p.mountpoint)), default=0)
                worst = max(cpu, ram, disk)
                message = ("الحالة: حرجة" if worst >= 90 else
                           "الحالة: تحتاج انتباه" if worst >= 75 else "الحالة: جيدة")
                self.after(0, lambda: (self.health.config(
                    text=f"{message} — CPU {cpu:.0f}% | RAM {ram:.0f}% | Disk {disk:.0f}%"),
                    self.status.config(text="اكتمل الفحص")))
            except Exception as exc:
                self.after(0, lambda: self.status.config(text=f"فشل الفحص: {exc}"))
        threading.Thread(target=worker, daemon=True).start()

    def clean_temp(self) -> None:
        if not messagebox.askyesno("تنظيف", "حذف الملفات المؤقتة للمستخدم الحالي؟"):
            return
        temp = os.environ.get("TEMP") or os.environ.get("TMP")
        deleted = 0
        if temp and os.path.isdir(temp):
            for root, dirs, files in os.walk(temp, topdown=False):
                for name in files:
                    try:
                        os.remove(os.path.join(root, name))
                        deleted += 1
                    except OSError:
                        pass
                for name in dirs:
                    try:
                        os.rmdir(os.path.join(root, name))
                    except OSError:
                        pass
        messagebox.showinfo("التنظيف", f"تم حذف {deleted} ملف تقريبًا.")

    def refresh_report(self) -> None:
        data = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "computer": socket.gethostname(),
            "platform": platform.platform(),
            "windows": platform.version(),
            "python": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(None),
            "memory_percent": psutil.virtual_memory().percent,
            "process_count": len(psutil.pids()),
            "admin": is_admin(),
            "disks": [],
        }
        for p in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(p.mountpoint)
                data["disks"].append({
                    "device": p.device,
                    "total_gb": round(usage.total / 1024**3, 2),
                    "free_gb": round(usage.free / 1024**3, 2),
                    "used_percent": usage.percent,
                })
            except OSError:
                pass
        self.report_data = data
        self.replace(self.report, json.dumps(data, ensure_ascii=False, indent=2))

    def save_txt(self) -> None:
        if not hasattr(self, "report_data"):
            self.refresh_report()
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text", "*.txt")])
        if path:
            Path(path).write_text(self.report.get("1.0", "end"), encoding="utf-8")
            messagebox.showinfo("التقرير", "تم حفظ التقرير.")

    def save_json(self) -> None:
        if not hasattr(self, "report_data"):
            self.refresh_report()
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON", "*.json")])
        if path:
            Path(path).write_text(json.dumps(self.report_data, ensure_ascii=False, indent=2),
                                  encoding="utf-8")
            messagebox.showinfo("التقرير", "تم حفظ JSON.")

    @staticmethod
    def replace(widget: tk.Text, text: str) -> None:
        widget.delete("1.0", "end")
        widget.insert("end", text)

    @staticmethod
    def uptime() -> str:
        seconds = max(0, int(datetime.now().timestamp() - psutil.boot_time()))
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        return f"{days} يوم، {hours} ساعة"


def run() -> None:
    App().mainloop()
