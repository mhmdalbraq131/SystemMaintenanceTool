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
import tkinter.font as tkfont
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
# Standard application font used across all Arabic UI pages.
# The command console intentionally keeps Consolas for technical readability.
UI_FONT = "Arial"
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
        global UI_FONT
        try:
            if UI_FONT not in tkfont.families(self):
                UI_FONT = "Arial"
        except Exception:
            UI_FONT = "Arial"
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
        b=tk.Button(parent,text=text,command=command,
                     bg=ACCENT if primary else PANEL2,
                     fg="#00131b" if primary else TEXT,
                     activebackground="#38e8ff" if primary else "#17344b",
                     activeforeground="#00131b" if primary else "white",
                     relief="flat",bd=0,padx=18,pady=9,
                     font=(UI_FONT,9,"bold"),cursor="hand2")
        def enter(_): b.configure(bg="#38e8ff" if primary else "#17344b")
        def leave(_): b.configure(bg=ACCENT if primary else PANEL2)
        b.bind("<Enter>",enter); b.bind("<Leave>",leave)
        return b

    def _build_style(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                    rowheight=30, borderwidth=0)
        s.configure("Treeview.Heading", background=PANEL2, foreground=TEXT,
                    relief="flat", font=(UI_FONT, 9, "bold"))
        s.configure("TProgressbar", troughcolor="#07111f", background=ACCENT, borderwidth=0,
                    thickness=5)

    def _build_layout(self) -> None:
        # Modern WinAdmin-inspired shell: compact navigation + large command workspace.
        head=tk.Frame(self,bg="#050b13",height=72)
        head.pack(fill="x"); head.pack_propagate(False)

        brand=tk.Frame(head,bg="#050b13")
        brand.pack(side="right",fill="y",padx=22)
        tk.Label(brand,text="◈",bg="#050b13",fg=ACCENT,font=(UI_FONT,23,"bold")).pack(side="right",padx=(0,10),pady=10)
        names=tk.Frame(brand,bg="#050b13"); names.pack(side="right",pady=10)
        tk.Label(names,text="SYSTEM MAINTENANCE",bg="#050b13",fg=TEXT,font=(UI_FONT,13,"bold")).pack(anchor="e")
        tk.Label(names,text="Windows Administration Center",bg="#050b13",fg=MUTED,font=(UI_FONT,8)).pack(anchor="e")

        self.status=tk.Label(head,text="READY",bg="#050b13",fg=GOOD,font=("Consolas",9,"bold"))
        self.status.pack(side="left",padx=22)
        tk.Label(head,text="● ONLINE",bg="#050b13",fg=GOOD,font=("Consolas",9,"bold")).pack(side="left",padx=8)

        body=tk.Frame(self,bg=BG); body.pack(fill="both",expand=True)
        nav=tk.Frame(body,bg="#060d17",width=245,highlightthickness=1,highlightbackground="#102337")
        nav.pack(side="right",fill="y"); nav.pack_propagate(False)

        tk.Label(nav,text="WORKSPACE",bg="#060d17",fg=MUTED,font=("Consolas",8,"bold")).pack(fill="x",padx=18,pady=(20,8))
        self.buttons={}
        items=[
            ("dashboard","⌂","لوحة المعلومات","OVERVIEW"),
            ("system","▣","معلومات النظام","SYSTEM"),
            ("processes","◉","العمليات","PROCESSES"),
            ("devices","◈","الأجهزة والتعريفات","DEVICES"),
            ("storage","▤","التخزين","STORAGE"),
            ("network","⌁","الشبكة","NETWORK"),
            ("security","◆","الأمان","SECURITY"),
            ("events","◌","سجل الأحداث","EVENTS"),
            ("maintenance","⚙","الصيانة والإصلاح","MAINTENANCE"),
            ("services","▤","خدمات Windows","SERVICES"),
            ("startup","↗","بدء التشغيل","STARTUP"),
            ("software","▦","البرامج المثبتة","SOFTWARE"),
            ("commands","⌘","مركز الأوامر","COMMAND CENTER"),
            ("reports","▥","التقارير","REPORTS"),
        ]
        for key,icon,title,code in items:
            b=tk.Button(nav,text=f"{icon}   {title}",command=lambda k=key:self.show(k),
                        bg="#060d17",fg=TEXT,activebackground="#102c40",activeforeground="white",
                        relief="flat",bd=0,anchor="e",padx=18,pady=8,
                        font=(UI_FONT,9),cursor="hand2")
            b.pack(fill="x",padx=9,pady=1); self.buttons[key]=b

        foot=tk.Frame(nav,bg="#060d17"); foot.pack(side="bottom",fill="x",padx=18,pady=16)
        tk.Frame(foot,bg="#123049",height=1).pack(fill="x",pady=(0,10))
        tk.Label(foot,text=("ADMINISTRATOR" if is_admin() else "STANDARD USER"),bg="#060d17",
                 fg=GOOD if is_admin() else WARN,font=("Consolas",8,"bold")).pack(anchor="e")
        tk.Label(foot,text="Native Windows tools • No cloud",bg="#060d17",fg=MUTED,font=(UI_FONT,7)).pack(anchor="e",pady=(3,0))

        self.content=tk.Frame(body,bg=BG); self.content.pack(side="left",fill="both",expand=True)
        self.pages={}
        for key,_,title,_ in items: self.page(key,title)
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
            tk.Label(bar, text=title, bg=BG, fg=TEXT, font=(UI_FONT, 20, "bold")).pack(side="right")
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
        f=self.pages["dashboard"]
        hero=tk.Frame(f,bg=BG); hero.pack(fill="x",padx=28,pady=(22,10))
        left=tk.Frame(hero,bg=BG); left.pack(side="left")
        tk.Label(left,text="LIVE SYSTEM MONITOR",bg=BG,fg=ACCENT,font=("Consolas",9,"bold")).pack(anchor="w")
        tk.Label(left,text="مركز مراقبة النظام",bg=BG,fg=TEXT,font=(UI_FONT,24,"bold")).pack(anchor="w",pady=(3,0))
        tk.Label(left,text="مؤشرات مباشرة • تشخيص • صيانة • أوامر",bg=BG,fg=MUTED,font=(UI_FONT,9)).pack(anchor="w")
        right=tk.Frame(hero,bg=PANEL,highlightthickness=1,highlightbackground="#153149")
        right.pack(side="right",ipadx=14,ipady=9)
        self.health=tk.Label(right,text="● النظام مستقر",bg=PANEL,fg=GOOD,font=(UI_FONT,10,"bold"))
        self.health.pack(anchor="e")
        self.health_detail=tk.Label(right,text="جاري قراءة المؤشرات...",bg=PANEL,fg=MUTED,font=(UI_FONT,8))
        self.health_detail.pack(anchor="e",pady=(2,0))

        gauges=tk.Frame(f,bg=BG); gauges.pack(fill="x",padx=22,pady=4)
        for i in range(3): gauges.grid_columnconfigure(i,weight=1,uniform="g")
        self.gauges={}
        for col,(key,title,code,accent) in enumerate([
            ("cpu","المعالج","CPU LOAD",ACCENT),("ram","الذاكرة","MEMORY",ACCENT2),("disk","التخزين","DISK",WARN)]):
            card=tk.Frame(gauges,bg=PANEL,highlightthickness=1,highlightbackground="#12283b")
            card.grid(row=0,column=col,sticky="nsew",padx=6)
            tk.Label(card,text=code,bg=PANEL,fg=accent,font=("Consolas",8,"bold")).pack(anchor="e",padx=16,pady=(11,0))
            cv=tk.Canvas(card,width=270,height=220,bg=PANEL,highlightthickness=0,bd=0)
            cv.pack(fill="both",expand=True)
            val=tk.Label(card,text="0%",bg=PANEL,fg=TEXT,font=("Consolas",18,"bold"))
            val.pack(pady=(0,1))
            tk.Label(card,text=title,bg=PANEL,fg=MUTED,font=(UI_FONT,9)).pack(pady=(0,10))
            self.gauges[key]={"canvas":cv,"value":val,"accent":accent}
            self._draw_gauge(key,0)

        strip=tk.Frame(f,bg="#06101b",highlightthickness=1,highlightbackground="#112a3e")
        strip.pack(fill="x",padx=28,pady=12)
        self.dp=self._telemetry_item(strip,"العمليات","PROCESSES")
        self.du=self._telemetry_item(strip,"مدة التشغيل","UPTIME")
        self.da=self._telemetry_item(strip,"الصلاحيات","ADMIN")
        self.speed=self._telemetry_item(strip,"سرعة المعالج","CLOCK")
        self.net=self._telemetry_item(strip,"الشبكة","NETWORK")

        actions=tk.Frame(f,bg=BG); actions.pack(fill="x",padx=28,pady=(2,0))
        tk.Label(actions,text="الوصول السريع",bg=BG,fg=TEXT,font=(UI_FONT,11,"bold")).pack(anchor="e",pady=(0,7))
        row=tk.Frame(actions,bg=BG); row.pack(fill="x")
        for title,fn,primary in [
            ("فحص صحة النظام",self.health_check,True),
            ("تنظيف المؤقتات",self.clean_temp,False),
            ("SFC",lambda:self.command(["sfc","/scannow"]),False),
            ("DNS",lambda:self.command(["ipconfig","/flushdns"]),False),
            ("مركز الأوامر",lambda:self.show("commands"),False)]:
            self._button(row,title,fn,primary).pack(side="right",padx=4)

    def _telemetry_item(self, parent, title, code):
        box = tk.Frame(parent, bg=PANEL)
        box.pack(side="right", fill="x", expand=True, padx=10, pady=10)
        tk.Label(box, text=code, bg=PANEL, fg=MUTED,
                 font=("Consolas", 7, "bold")).pack(anchor="e")
        value = tk.Label(box, text="—", bg=PANEL, fg=TEXT,
                         font=(UI_FONT, 12, "bold"))
        value.pack(anchor="e")
        tk.Label(box, text=title, bg=PANEL, fg=MUTED,
                 font=(UI_FONT, 8)).pack(anchor="e")
        return value

    def _draw_gauge(self,key,value):
        g=self.gauges[key]; c=g["canvas"]; c.delete("all")
        w=max(c.winfo_width(),270); cx=w/2; cy=112; r=86
        import math
        start,extent=135,270; v=max(0,min(100,float(value)))
        # Instrument bezel / face.
        c.create_oval(cx-r-13,cy-r-13,cx+r+13,cy+r+13,fill="#040a12",outline="#1d3448",width=2)
        c.create_oval(cx-r+8,cy-r+8,cx+r-8,cy+r-8,fill=PANEL,outline="#0c1b2b",width=2)
        # Danger band.
        c.create_arc(cx-r,cy-r,cx+r,cy+r,start=start+extent*.9,extent=extent*.1,
                     style="arc",outline=DANGER,width=10)
        c.create_arc(cx-r,cy-r,cx+r,cy+r,start=start,extent=extent,
                     style="arc",outline="#20374b",width=10)
        c.create_arc(cx-r,cy-r,cx+r,cy+r,start=start,extent=extent*v/100,
                     style="arc",outline=g["accent"],width=10)
        # Precision ticks.
        for i in range(41):
            pct=i/40; a=math.radians(start+extent*pct)
            ro=r+1; ri=r-(13 if i%4==0 else 8)
            x1,y1=cx+ro*math.cos(a),cy-ro*math.sin(a); x2,y2=cx+ri*math.cos(a),cy-ri*math.sin(a)
            c.create_line(x1,y1,x2,y2,fill="#9eb0bf" if i%4==0 else "#3a5368",width=2 if i%4==0 else 1)
        for n in (0,25,50,75,100):
            a=math.radians(start+extent*n/100); rr=r-25
            c.create_text(cx+rr*math.cos(a),cy-rr*math.sin(a),text=str(n),fill=MUTED,font=("Consolas",7,"bold"))
        # Needle and hub.
        a=math.radians(start+extent*v/100); nx,ny=cx+(r-20)*math.cos(a),cy-(r-20)*math.sin(a)
        c.create_line(cx,cy,nx,ny,fill="#eafcff",width=3)
        c.create_oval(cx-6,cy-6,cx+6,cy+6,fill=g["accent"],outline="#dff7ff",width=1)
        c.create_text(cx,cy+29,text=f"{v:.0f}%",fill=TEXT,font=("Consolas",18,"bold"))
        state="NORMAL" if v<75 else "HIGH" if v<90 else "CRITICAL"
        c.create_text(cx,cy+49,text=state,fill=g["accent"] if v<75 else WARN if v<90 else DANGER,font=("Consolas",7,"bold"))

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
        f=self.pages["storage"]
        self.storage=self.textbox(f)
        bar=tk.Frame(f,bg=BG); bar.pack(fill="x",padx=24,pady=5)
        self._button(bar,"فحص الأقراص",self.refresh_storage,True).pack(side="right",padx=3)
        self._button(bar,"صحة الأقراص",self.refresh_disk_health).pack(side="right",padx=3)
        self._button(bar,"إدارة الأقراص",lambda:self._async_custom("diskmgmt.msc")).pack(side="right",padx=3)
    def _network_controls(self):
        f=self.pages["network"]
        self.network=self.textbox(f)
        bar=tk.Frame(f,bg=BG); bar.pack(fill="x",padx=24,pady=5)
        self._button(bar,"فحص الشبكة",self.refresh_network,True).pack(side="right",padx=3)
        self._button(bar,"اختبار الاتصال",self.network_test).pack(side="right",padx=3)
        self._button(bar,"عرض الاتصالات",lambda:self._async_command(["netstat","-ano"],self.network,30)).pack(side="right",padx=3)
        self._button(bar,"إعدادات IP",lambda:self._async_command(["ipconfig","/all"],self.network,30)).pack(side="right",padx=3)
    def _security_controls(self):
        f=self.pages["security"]
        self.security=self.textbox(f,("Consolas",9))
        bar=tk.Frame(f,bg=BG); bar.pack(fill="x",padx=24,pady=5)
        self._button(bar,"فحص شامل",self.refresh_security,True).pack(side="right",padx=3)
        self._button(bar,"جدار الحماية",lambda:self._async_command(["netsh","advfirewall","show","allprofiles"],self.security,30)).pack(side="right",padx=3)
        self._button(bar,"Windows Security",lambda:self._async_custom("windowsdefender:")).pack(side="right",padx=3)
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
                 bg=BG,fg=(GOOD if is_admin() else WARN),font=(UI_FONT,10)).pack(anchor="e",padx=24,pady=10)
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
        tk.Label(panel,text="⌘  COMMAND CENTER",bg=PANEL,fg=ACCENT,font=("Consolas",12,"bold")).pack(side="left",padx=16,pady=11)
        tk.Label(panel,text="مكتبة أوامر Windows + محطة تنفيذ",bg=PANEL,fg=MUTED,font=(UI_FONT,9)).pack(side="right",padx=16,pady=11)

        main=tk.Frame(f,bg=BG); main.pack(fill="both",expand=True,padx=24,pady=6)
        library=tk.Frame(main,bg=PANEL,highlightthickness=1,highlightbackground="#15344b",width=365)
        library.pack(side="right",fill="y"); library.pack_propagate(False)

        tk.Label(library,text="مكتبة أوامر النظام",bg=PANEL,fg=TEXT,font=(UI_FONT,13,"bold")).pack(anchor="e",padx=14,pady=(14,2))
        tk.Label(library,text="اختر المجموعة ثم الأمر لمعرفة وظيفته",bg=PANEL,fg=MUTED,font=(UI_FONT,8)).pack(anchor="e",padx=14,pady=(0,8))

        top=tk.Frame(library,bg=PANEL); top.pack(fill="x",padx=10,pady=4)
        self.command_category=tk.StringVar(value="كل المجموعات")
        self.command_categories=ttk.Combobox(top,textvariable=self.command_category,state="readonly",
                                              values=["كل المجموعات"]+list(self.command_catalog.keys()),
                                              justify="right",font=(UI_FONT,9))
        self.command_categories.pack(fill="x"); self.command_categories.bind("<<ComboboxSelected>>",lambda e:self._populate_command_list())

        self.command_list=tk.Listbox(library,bg="#050c15",fg=TEXT,selectbackground="#10465c",
                                     selectforeground=ACCENT,activestyle="none",relief="flat",
                                     highlightthickness=0,font=(UI_FONT,9),justify="right")
        self.command_list.pack(fill="both",expand=True,padx=10,pady=8)
        self.command_list.bind("<<ListboxSelect>>",lambda e:self._command_selected())

        right=tk.Frame(main,bg=BG); right.pack(side="left",fill="both",expand=True,padx=(0,12))
        info=tk.Frame(right,bg=PANEL,highlightthickness=1,highlightbackground="#15344b")
        info.pack(fill="x",pady=(0,8))
        self.command_name=tk.Label(info,text="اختر أمرًا من المكتبة",bg=PANEL,fg=ACCENT,font=("Consolas",13,"bold"))
        self.command_name.pack(anchor="e",padx=16,pady=(13,2))
        self.command_description=tk.Label(info,text="سيظهر هنا شرح الأمر، فائدته، ونطاق استخدامه.",bg=PANEL,fg=TEXT,
                                          font=(UI_FONT,10),justify="right",anchor="e",wraplength=760)
        self.command_description.pack(fill="x",padx=16,pady=(0,5))
        self.command_safety=tk.Label(info,text="",bg=PANEL,fg=WARN,font=(UI_FONT,8),justify="right",anchor="e")
        self.command_safety.pack(fill="x",padx=16,pady=(0,11))
        tk.Label(info,text="ملاحظة: بعض أوامر الإدارة تحتاج تشغيل الأداة كمسؤول بسبب UAC.",bg=PANEL,fg=MUTED,font=(UI_FONT,8)).pack(anchor="e",padx=16,pady=(0,9))

        row=tk.Frame(right,bg=BG); row.pack(fill="x",pady=5)
        tk.Label(row,text="الأمر",bg=BG,fg=MUTED,font=("Consolas",8,"bold")).pack(side="right")
        self.cmd_entry=tk.Entry(row,bg="#020812",fg=ACCENT,insertbackground=ACCENT,relief="flat",
                                font=("Consolas",11)); self.cmd_entry.pack(side="right",fill="x",expand=True,ipady=10,padx=10)
        self._button(row,"تنفيذ  ▶",self.run_custom_command,True).pack(side="right")
        self.cmd_entry.bind("<Return>", lambda _e: self.run_custom_command())

        tk.Label(right,text="سجل التنفيذ",bg=BG,fg=TEXT,font=(UI_FONT,10,"bold")).pack(anchor="e",pady=(8,3))
        self.cmd_output=tk.Text(right,bg="#02050a",fg="#9be7ff",insertbackground=ACCENT,relief="flat",
                                wrap="none",font=("Consolas",10))
        self.cmd_output.pack(fill="both",expand=True)
        self.cmd_output.insert("end","SYSTEM MAINTENANCE TERMINAL\\n════════════════════════════════════════════════════════════\\nLINK: ONLINE    SHELL: CMD.EXE    MODE: ADMIN-AWARE\\n\\nPS> ")
        self.cmd_output.configure(state="disabled")

        self._populate_command_list()

    def _set_command(self, command: str) -> None:
        """Place a catalog command into the execution line."""
        self.cmd_entry.delete(0, "end")
        self.cmd_entry.insert(0, command)
        self.cmd_entry.focus_set()
        self.status.config(text="الأمر جاهز للتنفيذ")

    def _command_selected(self):
        sel=self.command_list.curselection()
        if not sel: return
        category=self.command_category.get()
        names=self._command_visible
        name=names[sel[0]]
        item=None
        for cat,items in self.command_catalog.items():
            if category=="كل المجموعات" or cat==category:
                for x in items:
                    if x[0]==name: item=x; break
            if item: break
        if not item: return
        command,description,safety=item[1],item[2],item[3]
        self.command_name.config(text=f"{name}  //  {command}")
        self.command_description.config(text=description)
        self.command_safety.config(text=safety)
        self._set_command(command)

    def _populate_command_list(self):
        category=self.command_category.get()
        names=[]
        if category=="كل المجموعات":
            for items in self.command_catalog.values(): names.extend([x[0] for x in items])
        else:
            names=[x[0] for x in self.command_catalog.get(category,[])]
        self._command_visible=names
        self.command_list.delete(0,"end")
        for name in names: self.command_list.insert("end",name)

    @property
    def command_catalog(self):
        return {
            "معلومات النظام":[
                ("systeminfo","systeminfo","يعرض إصدار Windows، بنية النظام، الذاكرة، وقت الإقلاع، الإصلاحات المثبتة ومعلومات أساسية عن الجهاز.","آمن للقراءة."),
                ("hostname","hostname","يعرض اسم الجهاز على الشبكة؛ مفيد للتعريف بالجهاز قبل تنفيذ الإدارة عن بُعد.","آمن للقراءة."),
                ("whoami","whoami /all","يعرض المستخدم الحالي، المجموعات، الامتيازات وبيانات جلسة الدخول.","آمن للقراءة."),
                ("ver","ver","يعرض إصدار Windows الحالي باختصار.","آمن للقراءة."),
                ("set","set","يعرض متغيرات البيئة المستخدمة في جلسة الأوامر؛ مفيد لتشخيص PATH وTEMP وغيرها.","آمن للقراءة."),
                ("driverquery","driverquery","يعرض تعريفات الأجهزة المحملة وحالتها؛ مفيد لتشخيص مشاكل التعريفات.","آمن للقراءة."),
                ("msinfo32","msinfo32","يفتح أداة معلومات النظام الرسومية للحصول على جرد شامل للعتاد والبرامج.","يفتح أداة Windows."),
            ],
            "العمليات والمهام":[
                ("tasklist","tasklist","يعرض جميع العمليات الجارية مع PID والذاكرة وغيرها؛ نقطة البداية لتحديد العمليات الثقيلة.","آمن للقراءة."),
                ("tasklist /svc","tasklist /svc","يربط العمليات بالخدمات التي تستضيفها؛ مفيد لمعرفة الخدمة المرتبطة بعملية معينة.","آمن للقراءة."),
                ("taskkill","taskkill /PID 1234 /T","ينهي عملية محددة بالـPID وجميع العمليات التابعة لها؛ استبدل 1234 بالمعرّف المطلوب.","تنبيه: ينهي العملية وقد تفقد بيانات غير محفوظة."),
                ("taskkill /force","taskkill /F /PID 1234 /T","إنهاء إجباري لعملية لا تستجيب؛ يستخدم كخيار أخير.","خطر متوسط: استخدمه فقط عند الحاجة."),
                ("resmon","resmon","يفتح Resource Monitor لمراقبة CPU والذاكرة والقرص والشبكة بالتفصيل.","يفتح أداة Windows."),
                ("perfmon","perfmon","يفتح Performance Monitor لتحليل مؤشرات الأداء وتسجيلها.","يفتح أداة Windows."),
            ],
            "الخدمات Services":[
                ("sc query","sc query","يعرض خدمات Windows وحالتها الحالية؛ مفيد للتشخيص السريع.","آمن للقراءة."),
                ("sc queryex","sc queryex type= service state= all","يعرض الخدمات مع PID والمعلومات الموسعة.","آمن للقراءة."),
                ("sc start","sc start Spooler","يشغّل خدمة محددة مثل Spooler؛ يجب استبدال الاسم باسم الخدمة الحقيقي.","يغيّر حالة خدمة."),
                ("sc stop","sc stop Spooler","يوقف خدمة محددة؛ قد تتوقف وظائف تعتمد عليها.","يغيّر حالة خدمة."),
                ("sc config","sc config Spooler start= auto","يغيّر إعداد بدء الخدمة، مثل تلقائي أو يدوي أو معطل.","تنبيه: يغيّر إعدادات النظام."),
                ("net start","net start","يعرض الخدمات التي تعمل حاليًا.","آمن للقراءة."),
                ("net stop","net stop Spooler","يوقف خدمة بالاسم باستخدام واجهة Net القديمة.","يغيّر حالة خدمة."),
                ("services.msc","services.msc","يفتح وحدة إدارة خدمات Windows الرسومية.","يفتح أداة Windows."),
            ],
            "الشبكة Network":[
                ("ipconfig","ipconfig /all","يعرض عناوين IP وDNS والبوابة وDHCP لكل محول؛ أساسي لتشخيص الشبكة.","آمن للقراءة."),
                ("ipconfig /flushdns","ipconfig /flushdns","يمسح ذاكرة DNS المحلية لإجبار الجهاز على طلب سجلات DNS من جديد.","آمن نسبيًا."),
                ("ipconfig /release","ipconfig /release","يحرر عنوان DHCP الحالي للمحول؛ يستخدم في استكشاف مشاكل الحصول على IP.","يقطع الاتصال مؤقتًا."),
                ("ipconfig /renew","ipconfig /renew","يطلب عنوان DHCP جديدًا للمحول.","قد يعيد الاتصال بالشبكة."),
                ("ping","ping 1.1.1.1","يختبر الوصول إلى عنوان IP وقياس زمن الاستجابة وفقد الحزم.","آمن للقراءة."),
                ("tracert","tracert example.com","يتتبع المسار الشبكي إلى وجهة ويظهر نقاط العبور وزمنها.","آمن للقراءة."),
                ("pathping","pathping example.com","يجمع بين tracert وping لتحليل فقد الحزم وزمن الاستجابة على المسار.","آمن للقراءة."),
                ("nslookup","nslookup example.com","يفحص حل أسماء DNS ويعرض الخادم والنتيجة؛ مفيد لتشخيص DNS.","آمن للقراءة."),
                ("netstat","netstat -ano","يعرض الاتصالات والمنافذ وحالة TCP/UDP وPID المرتبط بها.","آمن للقراءة."),
                ("arp","arp -a","يعرض جدول ARP المحلي الذي يربط عناوين IP بعناوين MAC.","آمن للقراءة."),
                ("route","route print","يعرض جدول التوجيه المحلي والمسارات المستخدمة لإرسال الحزم.","آمن للقراءة."),
                ("getmac","getmac /v","يعرض عناوين MAC للمحولات؛ مفيد لجرد الشبكة.","آمن للقراءة."),
                ("netsh interface","netsh interface show interface","يعرض حالة واجهات الشبكة وأسمائها.","آمن للقراءة."),
                ("netsh firewall","netsh advfirewall show allprofiles","يعرض حالة ملفات تعريف جدار حماية Windows.","آمن للقراءة."),
            ],
            "التخزين والأقراص":[
                ("diskpart","diskpart","يفتح أداة إدارة الأقراص والأقسام على مستوى منخفض؛ قوية لإدارة الأقراص.","خطر مرتفع: أوامر داخل DiskPart قد تمسح أقسامًا."),
                ("chkdsk","chkdsk C: /scan","يفحص نظام ملفات القرص بحثًا عن أخطاء دون جدولة إصلاح شامل؛ مناسب للفحص الأولي.","قراءة/فحص؛ بعض أوضاع الإصلاح قد تتطلب إعادة تشغيل."),
                ("chkdsk /f","chkdsk C: /f","يفحص ويصلح أخطاء نظام الملفات؛ قد يطلب قفل القرص وإعادة التشغيل.","تنبيه: يغيّر نظام الملفات."),
                ("fsutil","fsutil volume diskfree C:","يعرض المساحة الحرة على وحدة تخزين؛ FSUtil يحتوي أوامر إدارية كثيرة.","آمن لهذا الاستخدام؛ بقية FSUtil قد تكون حساسة."),
                ("format","format X:","يهيئ وحدة تخزين بنظام ملفات جديد.","خطر مرتفع: قد يمسح البيانات."),
                ("mountvol","mountvol","يعرض نقاط تركيب وحدات التخزين ومعرّفاتها.","آمن للقراءة."),
                ("diskmgmt.msc","diskmgmt.msc","يفتح إدارة الأقراص الرسومية لإنشاء وتوسيع وتقليص وإدارة وحدات التخزين.","يفتح أداة إدارية."),
            ],
            "إصلاح وصيانة Windows":[
                ("sfc /scannow","sfc /scannow","يفحص ملفات نظام Windows المحمية ويستبدل الملفات التالفة بنسخ سليمة عندما يستطيع.","إصلاح فعلي؛ يفضّل تشغيله كمسؤول."),
                ("DISM CheckHealth","DISM /Online /Cleanup-Image /CheckHealth","يتحقق سريعًا مما إذا كانت صورة Windows موسومة بوجود تلف معروف.","آمن للفحص."),
                ("DISM ScanHealth","DISM /Online /Cleanup-Image /ScanHealth","يفحص صورة Windows بعمق بحثًا عن تلف في مكونات النظام.","فحص قد يستغرق وقتًا."),
                ("DISM RestoreHealth","DISM /Online /Cleanup-Image /RestoreHealth","يحاول إصلاح تلف مكونات Windows باستخدام مصادر الإصلاح المتاحة.","إصلاح فعلي؛ قد يحتاج اتصالًا ومصدر Windows."),
                ("DISM StartComponentCleanup","DISM /Online /Cleanup-Image /StartComponentCleanup","ينظف الإصدارات القديمة من مكونات Windows التي لم تعد مطلوبة.","تنظيف؛ لا تشغله أثناء تحديثات حساسة."),
                ("gpupdate","gpupdate /force","يعيد تطبيق Group Policy على الجهاز والمستخدم فورًا؛ مفيد بعد تغيير سياسات المؤسسة.","قد يطبق سياسات إدارية فورًا."),
                ("gpresult","gpresult /h gpresult.html","ينشئ تقريرًا عن Group Policy المطبقة على المستخدم والجهاز.","يكتب ملف تقرير في المسار الحالي."),
                ("powercfg","powercfg /getactivescheme","يعرض خطة الطاقة النشطة؛ مفيد لتشخيص أداء الطاقة.","آمن للقراءة."),
                ("cleanmgr","cleanmgr","يفتح أداة تنظيف القرص القديمة المتوفرة في إصدارات Windows التي تدعمها.","يفتح أداة Windows."),
            ],
            "الأمان Security":[
                ("net user","net user","يعرض حسابات المستخدمين المحليين؛ مفيد لجرد الحسابات.","آمن للقراءة."),
                ("net localgroup","net localgroup","يعرض المجموعات المحلية وأعضاءها؛ مفيد لمراجعة الامتيازات.","آمن للقراءة."),
                ("whoami /groups","whoami /groups","يعرض مجموعات المستخدم الحالي وعضويته الفعلية.","آمن للقراءة."),
                ("whoami /priv","whoami /priv","يعرض الامتيازات التي يملكها رمز أمان المستخدم الحالي.","آمن للقراءة."),
                ("auditpol","auditpol /get /category:*","يعرض إعدادات تدقيق Windows الحالية؛ مفيد لمراجعة سياسة التدقيق.","قراءة للإعدادات."),
                ("wevtutil","wevtutil el","يعرض سجلات الأحداث المسجلة على الجهاز.","آمن للقراءة."),
                ("netsh advfirewall","netsh advfirewall show allprofiles","يعرض إعدادات جدار الحماية لكل ملفات التعريف.","آمن للقراءة."),
                ("secpol.msc","secpol.msc","يفتح Local Security Policy لإدارة سياسات الأمان المحلية.","أداة إدارية؛ لا تغيّر شيئًا دون معرفة الأثر."),
            ],
            "سجل الأحداث":[
                ("wevtutil el","wevtutil el","يسرد أسماء سجلات أحداث Windows المتاحة.","آمن للقراءة."),
                ("wevtutil qe","wevtutil qe System /c:20 /f:text","يعرض آخر 20 حدثًا من سجل System بصيغة نصية.","آمن للقراءة."),
                ("wevtutil gli","wevtutil gli System","يعرض خصائص سجل أحداث محدد مثل الحجم وموقع الملف.","آمن للقراءة."),
                ("eventvwr.msc","eventvwr.msc","يفتح Event Viewer لتحليل الأخطاء والتحذيرات والأحداث الأمنية.","يفتح أداة Windows."),
                ("eventcreate","eventcreate /T INFORMATION /ID 100 /L APPLICATION /SO SystemMaintenanceTool /D Test","ينشئ حدثًا مخصصًا في سجل الأحداث؛ مفيد للاختبار والتكامل.","يكتب حدثًا جديدًا في السجل."),
            ],
            "المستخدمون والصلاحيات":[
                ("net user list","net user","يسرد الحسابات المحلية على الجهاز.","آمن للقراءة."),
                ("net user details","net user Administrator","يعرض تفاصيل حساب محدد؛ استبدل Administrator باسم الحساب.","آمن للقراءة."),
                ("net localgroup administrators","net localgroup Administrators","يعرض أعضاء مجموعة Administrators المحلية.","آمن للقراءة."),
                ("query user","query user","يعرض جلسات المستخدمين الحالية وحالتها ووقت الدخول.","آمن للقراءة."),
                ("quser","quser","اختصار لعرض جلسات المستخدمين المتصلين.","آمن للقراءة."),
                ("whoami /user","whoami /user","يعرض اسم المستخدم الحالي ومعرّف الأمان SID.","آمن للقراءة."),
            ],
            "بدء التشغيل والمهام المجدولة":[
                ("schtasks /query","schtasks /query /fo TABLE /v","يعرض المهام المجدولة وتفاصيل تشغيلها؛ مفيد لاكتشاف مهام بدء التشغيل والصيانة.","آمن للقراءة."),
                ("schtasks /query /fo CSV","schtasks /query /fo CSV /nh","يصدر قائمة المهام المجدولة بصيغة CSV مناسبة للتحليل.","آمن للقراءة."),
                ("schtasks /run","schtasks /run /tn \"اسم المهمة\"","يشغل مهمة مجدولة يدويًا؛ استبدل الاسم بالمسار الحقيقي للمهمة.","ينفذ مهمة على الجهاز."),
                ("schtasks /end","schtasks /end /tn \"اسم المهمة\"","ينهي تشغيل مهمة مجدولة حاليًا.","يوقف مهمة جارية."),
                ("msconfig","msconfig","يفتح System Configuration لإدارة خيارات الإقلاع والخدمات وأدوات التشخيص.","أداة حساسة؛ تغييراتها تؤثر على الإقلاع."),
            ],
            "الملفات والملكية":[
                ("dir","dir","يعرض الملفات والمجلدات في مسار محدد؛ مفيد للجرد السريع.","آمن للقراءة."),
                ("tree","tree /F","يعرض هيكل المجلدات والملفات بشكل شجري.","آمن للقراءة."),
                ("where","where python","يبحث عن مسار ملف تنفيذي في PATH؛ مفيد لتشخيص تعارض الإصدارات.","آمن للقراءة."),
                ("robocopy","robocopy C:\\Source D:\\Backup /E /L","يعرض ما الذي سيُنسخ بين مسارين باستخدام وضع المحاكاة /L؛ مناسب للتأكد قبل النسخ.","قراءة فقط مع /L؛ أزل /L فقط بعد المراجعة."),
                ("icacls","icacls C:\\Path","يعرض أذونات NTFS للمسار المحدد.","آمن للقراءة."),
                ("attrib","attrib","يعرض خصائص الملفات مثل مخفي وقراءة فقط.","آمن للقراءة."),
                ("compact","compact /q","يعرض حالة ضغط NTFS للمجلدات والملفات.","آمن للقراءة."),
            ],
            "السجل Registry":[
                ("reg query","reg query HKLM\\SOFTWARE","يقرأ مفاتيح وقيم Registry؛ مفيد لتشخيص إعدادات Windows والبرامج.","آمن للقراءة."),
                ("reg query Run","reg query HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run","يعرض برامج بدء التشغيل المسجلة للمستخدم الحالي.","آمن للقراءة."),
                ("reg export","reg export HKCU\\Software\\Example backup.reg","يصدّر مفتاح Registry إلى ملف للنسخ الاحتياطي قبل التعديل.","يكتب نسخة احتياطية إلى ملف."),
                ("regedit","regedit","يفتح محرر Registry الرسومي.","أداة حساسة؛ تغييرات Registry قد تعطل النظام."),
            ],
            "الطاقة والإقلاع":[
                ("powercfg /list","powercfg /list","يسرد خطط الطاقة المتاحة على الجهاز.","آمن للقراءة."),
                ("powercfg /energy","powercfg /energy","يحلل استهلاك الطاقة ومشاكل الكفاءة وينشئ تقريرًا.","فحص؛ قد يستغرق نحو دقيقة."),
                ("powercfg /batteryreport","powercfg /batteryreport","ينشئ تقرير HTML عن حالة واستخدام بطارية أجهزة Windows المحمولة.","يكتب تقريرًا في المسار الحالي."),
                ("shutdown /a","shutdown /a","يلغي عملية إيقاف التشغيل أو إعادة التشغيل المجدولة إذا كانت قابلة للإلغاء.","يؤثر على جلسة النظام."),
                ("shutdown /r","shutdown /r /t 60","يجدول إعادة تشغيل بعد 60 ثانية؛ غيّر المهلة حسب الحاجة.","خطر تشغيلي: قد تغلق البرامج."),
                ("bcdedit","bcdedit /enum","يعرض إعدادات Boot Configuration Data الحالية.","قراءة فقط؛ تعديل BCD حساس جدًا."),
            ],
            "الإدارة والأدوات":[
                ("computer management","compmgmt.msc","يفتح Computer Management ويجمع عدة وحدات إدارية في مكان واحد.","يفتح أداة إدارية."),
                ("device manager","devmgmt.msc","يفتح Device Manager لفحص الأجهزة والتعريفات والأخطاء.","يفتح أداة إدارية."),
                ("task manager","taskmgr","يفتح Task Manager لمراقبة العمليات والأداء.","يفتح أداة Windows."),
                ("system configuration","msconfig","يفتح System Configuration لإدارة الإقلاع والخدمات وخيارات التشخيص.","أداة حساسة."),
                ("programs and features","appwiz.cpl","يفتح قائمة البرامج المثبتة وإلغاء التثبيت التقليدية.","يفتح أداة Windows."),
                ("control panel","control","يفتح Control Panel.","يفتح أداة Windows."),
                ("computer properties","sysdm.cpl","يفتح System Properties لإعدادات اسم الجهاز والأداء والمتقدم.","يفتح إعدادات Windows."),
                ("network connections","ncpa.cpl","يفتح Network Connections لإدارة محولات الشبكة.","يفتح إعدادات Windows."),
                ("event viewer","eventvwr.msc","يفتح Event Viewer.","يفتح أداة Windows."),
                ("disk management","diskmgmt.msc","يفتح Disk Management.","يفتح أداة إدارية."),
                ("services","services.msc","يفتح إدارة الخدمات.","يفتح أداة إدارية."),
            ],
        }

    def run_custom_command(self):
        raw=self.cmd_entry.get().strip()
        if not raw: return
        if not messagebox.askyesno("تأكيد التنفيذ",f"سيتم تنفيذ الأمر التالي:\\n\\n{raw}\\n\\nهل تريد المتابعة؟"): return
        self._async_custom(raw)

    def _async_custom(self,raw):
        self._console_write("\\nPS> "+raw+"\\n")
        def worker():
            try:
                code,out=run_native(["cmd","/c",raw],900)
                self.after(0,lambda:self._console_write(f"{out}\\n\\n[EXIT {code}]\\nPS> "))
            except Exception as exc:
                self.after(0,lambda:self._console_write(f"ERROR: {exc}\\nPS> "))
        threading.Thread(target=worker,daemon=True).start()

    def _console_write(self,text):
        self.cmd_output.configure(state="normal"); self.cmd_output.insert("end",text); self.cmd_output.see("end"); self.cmd_output.configure(state="disabled")

    def _report_controls(self):
        f=self.pages["reports"]; self.report=self.textbox(f,("Consolas",9)); bar=tk.Frame(f,bg=BG); bar.pack(fill="x",padx=24,pady=5)
        self._button(bar,"توليد التقرير",self.refresh_report,True).pack(side="right"); self._button(bar,"حفظ TXT",self.save_txt).pack(side="right",padx=5); self._button(bar,"حفظ JSON",self.save_json).pack(side="right")
    def textbox(self,parent,font=(UI_FONT,10)):
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
                for av in wmi.WMI().query("SELECT displayName, productState FROM AntiVirusProduct"):
                    lines.append(f"مكافح الفيروسات: {av.displayName} | الحالة: {av.productState}")
            except Exception as exc:
                lines.append(f"تعذر قراءة WMI للأمان: {exc}")
        ps=r'''
$fw=Get-NetFirewallProfile | Select-Object Name,Enabled,DefaultInboundAction,DefaultOutboundAction
$def=Get-MpComputerStatus -ErrorAction SilentlyContinue | Select-Object AMServiceEnabled,AntivirusEnabled,RealTimeProtectionEnabled,AntispywareEnabled,AntivirusSignatureVersion
"--- WINDOWS FIREWALL ---"
$fw | Format-Table -AutoSize
"--- MICROSOFT DEFENDER ---"
$def | Format-List
'''
        def worker():
            try:
                code,out=run_native(["powershell","-NoProfile","-Command",ps],30)
                text="\n".join(lines)+"\n\n"+out
                self.after(0,lambda:self.replace(self.security,text))
            except Exception as exc:
                self.after(0,lambda:self.replace(self.security,"\n".join(lines)+f"\n{exc}"))
        threading.Thread(target=worker,daemon=True).start()
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

    def refresh_disk_health(self):
        ps=r'Get-PhysicalDisk | Select-Object FriendlyName,MediaType,HealthStatus,OperationalStatus,Size | Format-Table -AutoSize'
        self._async_command(["powershell","-NoProfile","-Command",ps],self.storage,30)

    def network_test(self):
        ps=r'''
"=== PING 1.1.1.1 ==="
ping.exe -n 4 1.1.1.1
"=== DNS TEST ==="
Resolve-DnsName example.com -ErrorAction SilentlyContinue | Select-Object Name,Type,IPAddress | Format-Table -AutoSize
"=== DEFAULT GATEWAY ==="
Get-NetIPConfiguration | Where-Object {$_.IPv4DefaultGateway} | Select-Object InterfaceAlias,IPv4Address,IPv4DefaultGateway | Format-Table -AutoSize
'''
        self._async_command(["powershell","-NoProfile","-Command",ps],self.network,45)

    def refresh_services(self): self._async_command(["sc","query","type=","service","state=","all"],self.services,20)
    def refresh_startup(self): self._async_command(["reg","query",r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"],self.startup,15)
    def command(self,cmd):
        if not messagebox.askyesno("تأكيد","سيتم تنفيذ عملية صيانة في Windows. المتابعة؟"): return
        self.status.config(text="جاري تنفيذ العملية..."); self._async_command(cmd,None,900,show_window=True)
    def run_custom_command(self):
        raw=self.cmd_entry.get().strip()
        if not raw:
            messagebox.showwarning("مركز الأوامر","اختر أمرًا من المكتبة أو اكتب أمرًا أولًا.")
            self.status.config(text="لا يوجد أمر للتنفيذ")
            return
        if not messagebox.askyesno("تأكيد التنفيذ",f"سيتم تنفيذ الأمر التالي:\n\n{raw}\n\nهل تريد المتابعة؟"):
            return
        self._async_custom(raw)
    def _async_custom(self,raw):
        raw = raw.strip()
        if not raw:
            return
        self._console_write("\nPS> "+raw+"\n")
        self.status.config(text="جاري تنفيذ الأمر...")
        def worker():
            try:
                # /d disables CMD AutoRun entries and /s preserves normal CMD parsing.
                code,out=run_native(["cmd.exe","/d","/s","/c",raw],900)
                result = out or "(لا يوجد مخرجات — إذا كان الأمر رسوميًا فستظهر نافذة مستقلة.)"
                self.after(0,lambda:self._console_write(f"{result}\n\n[EXIT {code}]\nPS> "))
                self.after(0,lambda:self.status.config(text=("اكتمل التنفيذ" if code == 0 else f"فشل التنفيذ — Exit {code}")))
            except Exception as exc:
                self.after(0,lambda:self._console_write(f"ERROR: {exc}\nPS> "))
                self.after(0,lambda:self.status.config(text="خطأ أثناء التنفيذ"))
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
