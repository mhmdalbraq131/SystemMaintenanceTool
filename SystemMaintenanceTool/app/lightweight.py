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
    p = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=timeout, creationflags=flags)
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

    def _button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command,
                         bg="#0c4050" if primary else PANEL2,
                         fg=ACCENT if primary else TEXT,
                         activebackground="#155e75", activeforeground="white",
                         relief="flat", bd=0, padx=16, pady=9,
                         font=("Consolas", 9, "bold"), cursor="hand2")

    def _build_style(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                    rowheight=30, borderwidth=0)
        s.configure("Treeview.Heading", background=PANEL2, foreground=TEXT,
                    relief="flat", font=("Segoe UI", 9, "bold"))
        s.configure("TProgressbar", troughcolor="#07111f", background=ACCENT, borderwidth=0,
                    thickness=5)

    def _build_layout(self) -> None:
        head = tk.Frame(self, bg="#040a14", height=70)
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
        nav = tk.Frame(body, bg=PANEL, width=235)
        nav.pack(side="right", fill="y")
        nav.pack_propagate(False)
        tk.Label(nav, text="◈ FLIGHT SYSTEMS", bg=PANEL, fg=ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(fill="x", padx=18, pady=(22, 4))
        tk.Label(nav, text="مركز قيادة وصيانة النظام", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9)).pack(fill="x", padx=18, pady=(0, 12))
        tk.Frame(nav, bg=ACCENT, height=1).pack(fill="x", padx=18, pady=(0, 10))
        items = [
            ("dashboard", "⌂  لوحة المعلومات"), ("system", "▣  معلومات النظام"),
            ("processes", "◉  العمليات"), ("devices", "◈  الأجهزة والتعريفات"),
            ("storage", "▤  التخزين"), ("network", "⌁  الشبكة"), ("security", "◆  الأمان"),
            ("events", "◌  سجل الأحداث"), ("maintenance", "⚙  الصيانة والإصلاح"),
            ("services", "▤  خدمات Windows"), ("startup", "↗  بدء التشغيل"),
            ("software", "▦  البرامج المثبتة"), ("commands", "⌘  مركز الأوامر"),
            ("reports", "▥  التقارير"),
        ]
        self.buttons = {}
        for key, title in items:
            b = tk.Button(nav, text=title, command=lambda k=key: self.show(k), bg=PANEL, fg=TEXT,
                          activebackground="#12384a", activeforeground="white", relief="flat", bd=0,
                          anchor="e", padx=18, pady=9, font=("Segoe UI", 10), cursor="hand2")
            b.pack(fill="x", padx=8, pady=1)
            self.buttons[key] = b
        self.content = tk.Frame(body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        self.pages = {}
        for key, title in items:
            self.page(key, title)
        self._dashboard_controls(); self._system_controls(); self._process_controls()
        self._devices_controls(); self._storage_controls(); self._network_controls()
        self._security_controls(); self._events_controls(); self._maintenance_controls()
        self._service_controls(); self._startup_controls(); self._software_controls()
        self._command_controls(); self._report_controls()

    def page(self, key: str, title: str) -> tk.Frame:
        frame = tk.Frame(self.content, bg=BG)
        self.pages[key] = frame
        if key != "dashboard":
            bar = tk.Frame(frame, bg=BG)
            bar.pack(fill="x", padx=24, pady=(20, 12))
            tk.Label(bar, text=title, bg=BG, fg=TEXT, font=("Segoe UI", 20, "bold")).pack(side="right")
            tk.Label(bar, text=f"// {key.upper()}", bg=BG, fg=MUTED, font=("Consolas", 9)).pack(side="left", pady=8)
            tk.Frame(frame, bg="#16364a", height=1).pack(fill="x", padx=24, pady=(0, 10))
        return frame

    def show(self, key: str) -> None:
        for frame in self.pages.values(): frame.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        for k, button in self.buttons.items():
            button.configure(bg="#12384a" if k == key else PANEL, fg=ACCENT if k == key else TEXT)
        self.status.configure(text=self.buttons[key].cget("text"))

    def _dashboard_controls(self) -> None:
        f = self.pages["dashboard"]

        # Clean WinAdmin-inspired command-center header.
        top = tk.Frame(f, bg=BG)
        top.pack(fill="x", padx=28, pady=(18, 8))
        tk.Label(top, text="لوحة التحكم", bg=BG, fg=TEXT,
                 font=("Segoe UI", 24, "bold")).pack(side="right")
        tk.Label(top, text="SYSTEM OVERVIEW  /  LIVE TELEMETRY", bg=BG, fg=MUTED,
                 font=("Consolas", 9)).pack(side="left", pady=10)
        tk.Frame(f, bg="#1b3146", height=1).pack(fill="x", padx=28, pady=(0, 12))

        status = tk.Frame(f, bg=PANEL, highlightthickness=1, highlightbackground="#16334a")
        status.pack(fill="x", padx=28, pady=(0, 12))
        self.health = tk.Label(status, text="● النظام مستقر", bg=PANEL, fg=GOOD,
                               font=("Segoe UI", 11, "bold"))
        self.health.pack(side="right", padx=18, pady=11)
        self.health_detail = tk.Label(status, text="جاري قراءة مؤشرات النظام...", bg=PANEL,
                                      fg=MUTED, font=("Segoe UI", 9))
        self.health_detail.pack(side="left", padx=18, pady=11)

        # Three automotive-style analog gauges: CPU / RAM / DISK.
        gauges = tk.Frame(f, bg=BG)
        gauges.pack(fill="x", padx=22, pady=2)
        for i in range(3):
            gauges.grid_columnconfigure(i, weight=1, uniform="gauge")

        self.gauges = {}
        for col, (key, title, code, accent) in enumerate([
            ("cpu", "المعالج", "CPU LOAD", ACCENT),
            ("ram", "الذاكرة", "MEMORY", ACCENT2),
            ("disk", "التخزين", "DISK USAGE", WARN),
        ]):
            card = tk.Frame(gauges, bg=PANEL, highlightthickness=1, highlightbackground="#142b40")
            card.grid(row=0, column=col, sticky="nsew", padx=7)
            tk.Label(card, text=code, bg=PANEL, fg=accent,
                     font=("Consolas", 9, "bold")).pack(anchor="e", padx=16, pady=(12, 0))
            canvas = tk.Canvas(card, width=285, height=235, bg=PANEL, bd=0,
                               highlightthickness=0)
            canvas.pack(fill="both", expand=True, pady=(0, 4))
            value = tk.Label(card, text="0%", bg=PANEL, fg=TEXT,
                             font=("Consolas", 22, "bold"))
            value.pack(pady=(0, 1))
            tk.Label(card, text=title, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 10)).pack(pady=(0, 12))
            self.gauges[key] = {"canvas": canvas, "value": value, "accent": accent}
            self._draw_gauge(key, 0)

        # Compact telemetry strip, deliberately similar to a professional admin console.
        strip = tk.Frame(f, bg=PANEL, highlightthickness=1, highlightbackground="#142b40")
        strip.pack(fill="x", padx=28, pady=12)
        self.dp = self._telemetry_item(strip, "العمليات", "PROCESSES")
        self.du = self._telemetry_item(strip, "مدة التشغيل", "UPTIME")
        self.da = self._telemetry_item(strip, "الصلاحيات", "ADMIN")
        self.speed = self._telemetry_item(strip, "سرعة المعالج", "CLOCK")
        self.net = self._telemetry_item(strip, "الشبكة", "NETWORK")

        actions = tk.Frame(f, bg=BG)
        actions.pack(fill="x", padx=28, pady=2)
        tk.Label(actions, text="إجراءات سريعة", bg=BG, fg=TEXT,
                 font=("Segoe UI", 12, "bold")).pack(anchor="e", pady=(0, 7))
        row = tk.Frame(actions, bg=BG)
        row.pack(fill="x")
        for title, fn, primary in [
            ("فحص النظام", self.health_check, True),
            ("تنظيف المؤقتات", self.clean_temp, False),
            ("فحص SFC", lambda: self.command(["sfc", "/scannow"]), False),
            ("تفريغ DNS", lambda: self.command(["ipconfig", "/flushdns"]), False),
            ("محطة الأوامر", lambda: self.show("commands"), False),
        ]:
            self._button(row, title, fn, primary).pack(side="right", padx=4)

    def _telemetry_item(self, parent, title, code):
        box = tk.Frame(parent, bg=PANEL)
        box.pack(side="right", fill="x", expand=True, padx=10, pady=10)
        tk.Label(box, text=code, bg=PANEL, fg=MUTED,
                 font=("Consolas", 7, "bold")).pack(anchor="e")
        value = tk.Label(box, text="—", bg=PANEL, fg=TEXT,
                         font=("Segoe UI", 12, "bold"))
        value.pack(anchor="e")
        tk.Label(box, text=title, bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 8)).pack(anchor="e")
        return value

    def _draw_gauge(self, key, value):
        g = self.gauges[key]
        c = g["canvas"]
        c.delete("all")
        w = max(c.winfo_width(), 285)
        h = 235
        cx, cy = w / 2, 127
        r = 92
        start, extent = 135, 270

        # Outer bezel and segmented scale.
        c.create_oval(cx-r-9, cy-r-9, cx+r+9, cy+r+9,
                      outline="#10263a", width=2)
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=start, extent=extent,
                     style="arc", outline="#263b4d", width=13)
        c.create_arc(cx-r, cy-r, cx+r, cy+r, start=start, extent=extent*(max(0,min(100,value))/100),
                     style="arc", outline=g["accent"], width=13)

        import math
        for i in range(0, 21):
            pct = i / 20
            angle = math.radians(start + extent * pct)
            outer = r + 1
            inner = r - (15 if i % 2 == 0 else 9)
            x1, y1 = cx + outer*math.cos(angle), cy - outer*math.sin(angle)
            x2, y2 = cx + inner*math.cos(angle), cy - inner*math.sin(angle)
            c.create_line(x1, y1, x2, y2,
                          fill="#8aa0b4" if i % 2 == 0 else "#3c5368",
                          width=2 if i % 2 == 0 else 1)

        # Digital scale labels.
        for n in (0, 25, 50, 75, 100):
            pct = n / 100
            angle = math.radians(start + extent * pct)
            rr = r - 28
            x, y = cx + rr*math.cos(angle), cy - rr*math.sin(angle)
            c.create_text(x, y, text=str(n), fill=MUTED,
                          font=("Consolas", 8, "bold"))

        # Needle, like a performance gauge.
        angle = math.radians(start + extent * (max(0,min(100,value))/100))
        nx, ny = cx + (r-22)*math.cos(angle), cy - (r-22)*math.sin(angle)
        c.create_line(cx, cy, nx, ny, fill=TEXT, width=3)
        c.create_oval(cx-7, cy-7, cx+7, cy+7, fill=g["accent"], outline=TEXT, width=1)
        c.create_text(cx, cy+28, text=f"{value:.0f}%", fill=TEXT,
                      font=("Consolas", 20, "bold"))

    def _system_controls(self):
        f=self.pages["system"]; self.system=self.textbox(f); self._button(f,"تحديث",self.refresh_system,True).pack(anchor="e",padx=24,pady=5)
    def _process_controls(self):
        f=self.pages["processes"]
        bar=tk.Frame(f,bg=BG); bar.pack(fill="x",padx=24,pady=5)
        self._button(bar,"تحديث",self.refresh_processes,True).pack(side="right",padx=3)
        self._button(bar,"إنهاء المحدد",self.kill_selected_process).pack(side="right",padx=3)
        self._button(bar,"فتح مدير المهام",lambda:self._async_custom("taskmgr")).pack(side="right",padx=3)
        self.proc=self.tree(f,("pid","name","cpu","ram"),("PID","العملية","CPU %","RAM %"))
    def _storage_controls(self):
        f=self.pages["storage"]; self.storage=self.textbox(f); self._button(f,"فحص الأقراص",self.refresh_storage,True).pack(anchor="e",padx=24,pady=5)
    def _network_controls(self):
        f=self.pages["network"]; self.network=self.textbox(f); self._button(f,"فحص الشبكة",self.refresh_network,True).pack(anchor="e",padx=24,pady=5)
    def _security_controls(self):
        f=self.pages["security"]; self.security=self.textbox(f); self._button(f,"فحص الأمان",self.refresh_security,True).pack(anchor="e",padx=24,pady=5)
    def _maintenance_controls(self):
        f=self.pages["maintenance"]
        actions=[
            ("تنظيف الملفات المؤقتة",self.clean_temp),
            ("فحص ملفات Windows — SFC",lambda:self.command(["sfc","/scannow"])),
            ("فحص صحة Windows — DISM",lambda:self.command(["DISM","/Online","/Cleanup-Image","/CheckHealth"])),
            ("إصلاح صورة Windows — DISM",lambda:self.command(["DISM","/Online","/Cleanup-Image","/RestoreHealth"])),
            ("فحص القرص — CHKDSK",lambda:self.command(["chkdsk","C:","/scan"])),
            ("تفريغ DNS",lambda:self.command(["ipconfig","/flushdns"])),
            ("إعادة ضبط Winsock",lambda:self.command(["netsh","winsock","reset"])),
            ("تحديث سياسات النظام",lambda:self.command(["gpupdate","/force"])),
        ]
        for title,fn in actions: self._button(f,title,fn).pack(fill="x",padx=24,pady=3)
        tk.Label(f,text=("تشغيل كمسؤول: نعم" if is_admin() else "تنبيه: شغّل الأداة كمسؤول لتنفيذ إصلاحات Windows."),
                 bg=BG,fg=(GOOD if is_admin() else WARN),font=("Segoe UI",10)).pack(anchor="e",padx=24,pady=10)
    def _service_controls(self):
        f=self.pages["services"]
        bar=tk.Frame(f,bg=BG); bar.pack(fill="x",padx=24,pady=5)
        self._button(bar,"عرض الخدمات",self.refresh_services,True).pack(side="right",padx=3)
        self._button(bar,"تشغيل",lambda:self.service_action("start")).pack(side="right",padx=3)
        self._button(bar,"إيقاف",lambda:self.service_action("stop")).pack(side="right",padx=3)
        self._button(bar,"إعادة تشغيل",lambda:self.service_action("restart")).pack(side="right",padx=3)
        self.service_entry=tk.Entry(bar,bg=PANEL,fg=TEXT,insertbackground=ACCENT,relief="flat",font=("Consolas",10))
        self.service_entry.pack(side="right",fill="x",expand=True,ipady=8,padx=8)
        self.service_entry.insert(0,"اسم الخدمة مثل: Spooler")
        self.services=self.textbox(f,("Consolas",9))
    def _startup_controls(self):
        f=self.pages["startup"]; self.startup=self.textbox(f,("Consolas",9)); self._button(f,"فحص بدء التشغيل",self.refresh_startup,True).pack(anchor="e",padx=24,pady=5)
    def _devices_controls(self):
        f=self.pages["devices"]
        self.devices=self.textbox(f,("Consolas",9))
        bar=tk.Frame(f,bg=BG); bar.pack(fill="x",padx=24,pady=5)
        self._button(bar,"فحص الأجهزة",self.refresh_devices,True).pack(side="right",padx=3)
        self._button(bar,"التعريفات",self.refresh_drivers).pack(side="right",padx=3)
        self._button(bar,"إدارة الأجهزة",lambda:self._async_custom("devmgmt.msc")).pack(side="right",padx=3)

    def _events_controls(self):
        f=self.pages["events"]
        self.events=self.textbox(f,("Consolas",8))
        bar=tk.Frame(f,bg=BG); bar.pack(fill="x",padx=24,pady=5)
        self._button(bar,"أحدث أخطاء النظام",lambda:self.refresh_events("System","Error"),True).pack(side="right",padx=3)
        self._button(bar,"أحداث النظام",lambda:self.refresh_events("System","All")).pack(side="right",padx=3)
        self._button(bar,"أحداث التطبيقات",lambda:self.refresh_events("Application","All")).pack(side="right",padx=3)
        self._button(bar,"عارض الأحداث",lambda:self._async_custom("eventvwr.msc")).pack(side="right",padx=3)

    def _software_controls(self):
        f=self.pages["software"]
        self.software=self.textbox(f,("Consolas",8))
        bar=tk.Frame(f,bg=BG); bar.pack(fill="x",padx=24,pady=5)
        self._button(bar,"فحص البرامج",self.refresh_software,True).pack(side="right",padx=3)
        self._button(bar,"البرامج والميزات",lambda:self._async_custom("appwiz.cpl")).pack(side="right",padx=3)

    def _command_controls(self):
        f=self.pages["commands"]
        panel=tk.Frame(f,bg=PANEL,highlightthickness=1,highlightbackground="#15344b"); panel.pack(fill="x",padx=24,pady=(0,7))
        tk.Label(panel,text="⌘  COMMAND TERMINAL",bg=PANEL,fg=ACCENT,font=("Consolas",12,"bold")).pack(side="left",padx=16,pady=11)
        tk.Label(panel,text="محطة أوامر Windows المدمجة",bg=PANEL,fg=MUTED,font=("Segoe UI",9)).pack(side="right",padx=16,pady=11)
        quick=tk.Frame(f,bg=BG); quick.pack(fill="x",padx=24,pady=4)
        for label,cmd in [
            ("SYSTEMINFO","systeminfo"),("IPCONFIG","ipconfig /all"),("TASKLIST","tasklist"),
            ("NETSTAT","netstat -ano"),("SERVICES","sc query"),("DISK","wmic logicaldisk get caption,freespace,size"),
            ("POWER","powercfg /getactivescheme"),("WHOAMI","whoami /all")
        ]: self._button(quick,label,lambda c=cmd:self._set_command(c)).pack(side="right",padx=3)
        row=tk.Frame(f,bg=BG); row.pack(fill="x",padx=24,pady=6)
        self.cmd_entry=tk.Entry(row,bg="#020812",fg=ACCENT,insertbackground=ACCENT,relief="flat",font=("Consolas",12)); self.cmd_entry.pack(side="right",fill="x",expand=True,ipady=10,padx=(0,8))
        self._button(row,"EXECUTE  ▶",self.run_custom_command,True).pack(side="right")
        self.cmd_output=tk.Text(f,bg="#02050a",fg="#9be7ff",insertbackground=ACCENT,relief="flat",wrap="none",font=("Consolas",10)); self.cmd_output.pack(fill="both",expand=True,padx=24,pady=8)
        self.cmd_output.insert("end","SYSTEM MAINTENANCE TERMINAL\n════════════════════════════════════════════════════════════\nLINK: ONLINE    SHELL: CMD.EXE    MODE: ADMIN-AWARE\n\nPS> ")
        self.cmd_output.configure(state="disabled")
    def _set_command(self,value): self.cmd_entry.delete(0,"end"); self.cmd_entry.insert(0,value); self.cmd_entry.focus_set()
    def _report_controls(self):
        f=self.pages["reports"]; self.report=self.textbox(f,("Consolas",9)); bar=tk.Frame(f,bg=BG); bar.pack(fill="x",padx=24,pady=5)
        self._button(bar,"توليد التقرير",self.refresh_report,True).pack(side="right"); self._button(bar,"حفظ TXT",self.save_txt).pack(side="right",padx=5); self._button(bar,"حفظ JSON",self.save_json).pack(side="right")
    def textbox(self,parent,font=("Segoe UI",10)):
        t=tk.Text(parent,bg=PANEL,fg=TEXT,insertbackground=ACCENT,relief="flat",wrap="word",font=font); t.pack(fill="both",expand=True,padx=24,pady=6); return t
    def tree(self,parent,cols,heads):
        wrapper=tk.Frame(parent,bg=BG); wrapper.pack(fill="both",expand=True,padx=24,pady=6); tree=ttk.Treeview(wrapper,columns=cols,show="headings")
        for col,head in zip(cols,heads): tree.heading(col,text=head); tree.column(col,anchor="center",width=150)
        tree.pack(side="left",fill="both",expand=True); sb=ttk.Scrollbar(wrapper,orient="vertical",command=tree.yview); sb.pack(side="right",fill="y"); tree.configure(yscrollcommand=sb.set); return tree
    def _live_refresh(self): self.refresh_dashboard(); self.after(3500,self._live_refresh)
    def refresh_dashboard(self):
        try:
            cpu=psutil.cpu_percent(None); ram=psutil.virtual_memory().percent
            disk=max((psutil.disk_usage(p.mountpoint).percent for p in psutil.disk_partitions(all=False) if os.path.exists(p.mountpoint)),default=0)
            self._draw_gauge("cpu", cpu); self._draw_gauge("ram", ram); self._draw_gauge("disk", disk)
            procs=len(psutil.pids()); self.dp.config(text=str(procs)); self.du.config(text=self.uptime()); self.da.config(text="نعم" if is_admin() else "لا")
            try:
                freq=psutil.cpu_freq()
                self.speed.config(text=f"{freq.current/1000:.2f} GHz" if freq and freq.current else "—")
            except Exception:
                self.speed.config(text="—")
            self.net.config(text="متصل" if any(x.isup() for x in psutil.net_if_stats().values()) else "غير متصل")
            worst=max(cpu,ram,disk); state="● حالة حرجة" if worst>=90 else "● تحتاج انتباه" if worst>=75 else "● النظام مستقر"
            self.health.config(text=state)
            self.health_detail.config(text=f"CPU {cpu:.0f}%   •   RAM {ram:.0f}%   •   DISK {disk:.0f}%   •   PROCESSES {procs}")
        except Exception as exc: self.status.config(text=f"خطأ: {exc}")
    def refresh_system(self):
        lines=[f"اسم الجهاز: {socket.gethostname()}",f"النظام: {platform.platform()}",f"إصدار Windows: {platform.version()}",f"المعمارية: {platform.machine()}",f"Python: {platform.python_version()}",f"المعالج: {psutil.cpu_count(logical=False) or 0} أنوية فعلية / {psutil.cpu_count() or 0} منطقية",f"الذاكرة: {psutil.virtual_memory().total/1024**3:.2f} GB",f"الإقلاع: {datetime.fromtimestamp(psutil.boot_time()):%Y-%m-%d %H:%M:%S}",f"صلاحيات المسؤول: {'نعم' if is_admin() else 'لا'}"]; self.replace(self.system,"\n".join(lines))
    def refresh_processes(self):
        for item in self.proc.get_children(): self.proc.delete(item)
        rows=[]
        for process in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
            try: rows.append((process.info["pid"],process.info["name"] or "",process.info["cpu_percent"] or 0,process.info["memory_percent"] or 0))
            except (psutil.NoSuchProcess,psutil.AccessDenied): pass
        for row in sorted(rows,key=lambda x:x[2],reverse=True)[:150]: self.proc.insert("","end",values=(row[0],row[1],f"{row[2]:.1f}",f"{row[3]:.1f}"))
    def refresh_storage(self):
        out=[]
        for p in psutil.disk_partitions(all=False):
            try:
                u=psutil.disk_usage(p.mountpoint); out.append(f"{p.device}  {u.total/1024**3:.1f} GB | متاح {u.free/1024**3:.1f} GB | مستخدم {u.percent:.1f}%")
            except OSError: pass
        self.replace(self.storage,"\n".join(out) or "لم يتم العثور على أقراص.")
    def refresh_network(self):
        c=psutil.net_io_counters(); lines=[f"إرسال: {c.bytes_sent/1024**2:.1f} MB",f"استقبال: {c.bytes_recv/1024**2:.1f} MB",""]
        for name,addrs in psutil.net_if_addrs().items(): lines.append(name+":"); lines.extend("  "+addr.address for addr in addrs)
        self.replace(self.network,"\n".join(lines))
    def refresh_security(self):
        lines=[f"صلاحيات المسؤول: {'نعم' if is_admin() else 'لا'}"]
        if wmi:
            try:
                for av in wmi.WMI().query("SELECT displayName, productState FROM AntiVirusProduct"): lines.append(f"مكافح الفيروسات: {av.displayName} | الحالة: {av.productState}")
            except Exception as exc: lines.append(f"تعذر قراءة WMI للأمان: {exc}")
        else: lines.append("WMI غير متاح؛ تم استخدام الموارد الأساسية فقط.")
        self.replace(self.security,"\n".join(lines))
    def kill_selected_process(self):
        selected=self.proc.selection()
        if not selected:
            messagebox.showwarning("العمليات","حدد عملية أولًا.")
            return
        values=self.proc.item(selected[0],"values")
        pid=int(values[0]); name=values[1]
        if not messagebox.askyesno("إنهاء العملية",f"هل تريد إنهاء العملية؟\\n{name} (PID {pid})"):
            return
        self._async_command(["taskkill","/PID",str(pid),"/T"],None,30,show_window=True)

    def service_action(self, action):
        name=self.service_entry.get().strip()
        if not name or name.lower().startswith("اسم الخدمة"):
            messagebox.showwarning("الخدمات","اكتب اسم الخدمة.")
            return
        if action=="restart":
            cmd=["cmd","/c",f'sc stop "{name}" & sc start "{name}"']
        else:
            cmd=["sc",action,name]
        if messagebox.askyesno("الخدمات",f"تنفيذ {action} للخدمة {name}؟"):
            self._async_command(cmd,self.services,60)

    def refresh_devices(self):
        ps=r'Get-PnpDevice | Sort-Object Status,FriendlyName | Format-Table -AutoSize Status,Class,FriendlyName,InstanceId'
        self._async_command(["powershell","-NoProfile","-Command",ps],self.devices,30)

    def refresh_drivers(self):
        ps=r'Get-CimInstance Win32_PnPSignedDriver | Where-Object {$_.DeviceName} | Sort-Object DeviceName | Select-Object DeviceName,DriverVersion,DriverProviderName | Format-Table -AutoSize'
        self._async_command(["powershell","-NoProfile","-Command",ps],self.devices,30)

    def refresh_events(self, log_name="System", mode="All"):
        if mode=="Error":
            ps=f'Get-WinEvent -FilterHashtable @{{LogName="{log_name}"; Level=2}} -MaxEvents 50 | Format-List TimeCreated,ProviderName,Id,Message'
        else:
            ps=f'Get-WinEvent -LogName "{log_name}" -MaxEvents 50 | Format-List TimeCreated,ProviderName,Id,LevelDisplayName,Message'
        self._async_command(["powershell","-NoProfile","-Command",ps],self.events,45)

    def refresh_software(self):
        ps=r'$paths=@("HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*","HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*","HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*"); Get-ItemProperty $paths -ErrorAction SilentlyContinue | Where-Object {$_.DisplayName} | Sort-Object DisplayName -Unique | Select-Object DisplayName,DisplayVersion,Publisher | Format-Table -AutoSize'
        self._async_command(["powershell","-NoProfile","-Command",ps],self.software,45)

    def refresh_services(self): self._async_command(["sc","query","type=","service","state=","all"],self.services,20)
    def refresh_startup(self): self._async_command(["reg","query",r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"],self.startup,15)
    def command(self,cmd):
        if not messagebox.askyesno("تأكيد","سيتم تنفيذ عملية صيانة في Windows. المتابعة؟"): return
        self.status.config(text="جاري تنفيذ العملية..."); self._async_command(cmd,None,900,show_window=True)
    def run_custom_command(self):
        raw=self.cmd_entry.get().strip()
        if not raw: return
        if not messagebox.askyesno("تأكيد","تنفيذ الأمر كما كُتب؟"): return
        self._async_custom(raw)
    def _async_custom(self,raw):
        self._console_write("\nPS> "+raw+"\n")
        def worker():
            try:
                code,out=run_native(["cmd","/c",raw],900); self.after(0,lambda:self._console_write(f"{out}\n\n[EXIT {code}]\nPS> "))
            except Exception as exc: self.after(0,lambda:self._console_write(f"ERROR: {exc}\nPS> "))
        threading.Thread(target=worker,daemon=True).start()
    def _console_write(self,text): self.cmd_output.configure(state="normal"); self.cmd_output.insert("end",text); self.cmd_output.see("end"); self.cmd_output.configure(state="disabled")
    def _async_command(self,cmd,target,timeout,show_window=False):
        def worker():
            try:
                code,out=run_native(cmd,timeout); text=f"Exit code: {code}\n\n{out}"; self.after(0,lambda:self._command_done(target,text,show_window))
            except Exception as exc: self.after(0,lambda:self._command_done(target,str(exc),show_window))
        threading.Thread(target=worker,daemon=True).start()
    def _command_done(self,target,text,show_window):
        self.status.config(text="اكتملت العملية")
        if target is not None: self.replace(target,text)
        elif show_window:
            win=tk.Toplevel(self); win.title("نتيجة العملية"); win.geometry("900x560"); output=self.textbox(win,("Consolas",9)); self.replace(output,text)
    def health_check(self):
        self.status.config(text="جاري فحص الصحة...")
        def worker():
            try:
                cpu=psutil.cpu_percent(interval=1); ram=psutil.virtual_memory().percent; disk=max((psutil.disk_usage(p.mountpoint).percent for p in psutil.disk_partitions(all=False) if os.path.exists(p.mountpoint)),default=0); worst=max(cpu,ram,disk)
                message="الحالة: حرجة" if worst>=90 else "الحالة: تحتاج انتباه" if worst>=75 else "الحالة: جيدة"
                self.after(0,lambda:(self.health.config(text=f"{message} — CPU {cpu:.0f}% | RAM {ram:.0f}% | Disk {disk:.0f}%"),self.health_detail.config(text=f"CPU {cpu:.0f}%   •   RAM {ram:.0f}%   •   DISK {disk:.0f}%   •   فحص مكتمل"),self.status.config(text="اكتمل الفحص")))
            except Exception as exc: self.after(0,lambda:self.status.config(text=f"فشل الفحص: {exc}"))
        threading.Thread(target=worker,daemon=True).start()
    def clean_temp(self):
        if not messagebox.askyesno("تنظيف","حذف الملفات المؤقتة للمستخدم الحالي؟"): return
        temp=os.environ.get("TEMP") or os.environ.get("TMP"); deleted=0
        if temp and os.path.isdir(temp):
            for root,dirs,files in os.walk(temp,topdown=False):
                for name in files:
                    try: os.remove(os.path.join(root,name)); deleted+=1
                    except OSError: pass
                for name in dirs:
                    try: os.rmdir(os.path.join(root,name))
                    except OSError: pass
        messagebox.showinfo("التنظيف",f"تم حذف {deleted} ملف تقريبًا.")
    def refresh_report(self):
        vm=psutil.virtual_memory()
        data={"timestamp":datetime.now().isoformat(timespec="seconds"),"computer":socket.gethostname(),
              "platform":platform.platform(),"windows":platform.version(),"architecture":platform.machine(),
              "python":platform.python_version(),"cpu_percent":psutil.cpu_percent(None),
              "memory_percent":vm.percent,"memory_total_gb":round(vm.total/1024**3,2),
              "memory_available_gb":round(vm.available/1024**3,2),"process_count":len(psutil.pids()),
              "admin":is_admin(),"boot_time":datetime.fromtimestamp(psutil.boot_time()).isoformat(timespec="seconds"),
              "network_interfaces":list(psutil.net_if_stats().keys()),"disks":[]}
        for p in psutil.disk_partitions(all=False):
            try:
                u=psutil.disk_usage(p.mountpoint); data["disks"].append({"device":p.device,"total_gb":round(u.total/1024**3,2),"free_gb":round(u.free/1024**3,2),"used_percent":u.percent})
            except OSError: pass
        self.report_data=data; self.replace(self.report,json.dumps(data,ensure_ascii=False,indent=2))
    def save_txt(self):
        if not hasattr(self,"report_data"): self.refresh_report()
        path=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text","*.txt")])
        if path: Path(path).write_text(self.report.get("1.0","end"),encoding="utf-8"); messagebox.showinfo("التقرير","تم حفظ التقرير.")
    def save_json(self):
        if not hasattr(self,"report_data"): self.refresh_report()
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")])
        if path: Path(path).write_text(json.dumps(self.report_data,ensure_ascii=False,indent=2),encoding="utf-8"); messagebox.showinfo("التقرير","تم حفظ JSON.")
    @staticmethod
    def replace(widget,text): widget.delete("1.0","end"); widget.insert("end",text)
    @staticmethod
    def uptime():
        seconds=max(0,int(datetime.now().timestamp()-psutil.boot_time())); days,seconds=divmod(seconds,86400); hours,seconds=divmod(seconds,3600); return f"{days} يوم، {hours} ساعة"


def run(): App().mainloop()
