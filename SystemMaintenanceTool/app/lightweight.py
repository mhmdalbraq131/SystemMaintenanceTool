"""Lightweight native Windows UI for System Maintenance Tool."""
from __future__ import annotations
import ctypes, json, os, platform, socket, subprocess, threading, tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
import psutil
try:
    import wmi
except Exception:
    wmi = None
BG="#0f172a"; PANEL="#172033"; PANEL2="#1e293b"; TEXT="#e5e7eb"; MUTED="#94a3b8"; ACCENT="#2563eb"; WARN="#f59e0b"
def is_admin():
    try:return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:return False
def run_native(command,timeout=900):
    p=subprocess.run(command,capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0));return p.returncode,((p.stdout or "")+"\n"+(p.stderr or "")).strip()
class App(tk.Tk):
    def __init__(self):
        super().__init__();self.title("أداة صيانة النظام");self.geometry("1240x760");self.minsize(1000,640);self.configure(bg=BG);self.protocol("WM_DELETE_WINDOW",self.destroy);self._build_style();self._build_layout();self.show("dashboard");self.after(500,self.refresh_dashboard);self.after(3500,self._live_refresh)
    def _build_style(self):
        s=ttk.Style(self);s.theme_use("clam");s.configure("Treeview",background=PANEL,fieldbackground=PANEL,foreground=TEXT,rowheight=28,borderwidth=0);s.configure("Treeview.Heading",background=PANEL2,foreground=TEXT,relief="flat",font=("Segoe UI",9,"bold"));s.configure("TProgressbar",troughcolor=PANEL2,background=ACCENT,borderwidth=0)
    def _build_layout(self):
        head=tk.Frame(self,bg="#0b1220",height=66);head.pack(fill="x");tk.Label(head,text="أداة صيانة النظام",bg="#0b1220",fg="white",font=("Segoe UI",20,"bold")).pack(side="right",padx=24,pady=15);self.status=tk.Label(head,text="جاهز",bg="#0b1220",fg="#93c5fd",font=("Segoe UI",10));self.status.pack(side="left",padx=24)
        body=tk.Frame(self,bg=BG);body.pack(fill="both",expand=True);nav=tk.Frame(body,bg=PANEL,width=225);nav.pack(side="right",fill="y");nav.pack_propagate(False);tk.Label(nav,text="الإدارة والصيانة",bg=PANEL,fg=MUTED,font=("Segoe UI",10,"bold")).pack(fill="x",padx=18,pady=(22,10))
        self.buttons={}
        for key,title in [("dashboard","لوحة المعلومات"),("system","معلومات النظام"),("processes","العمليات"),("storage","التخزين"),("network","الشبكة"),("security","الأمان"),("maintenance","الصيانة والإصلاح"),("services","خدمات Windows"),("startup","بدء التشغيل"),("commands","مركز الأوامر"),("reports","التقارير")]:
            b=tk.Button(nav,text=title,command=lambda k=key:self.show(k),bg=PANEL,fg=TEXT,activebackground=ACCENT,activeforeground="white",relief="flat",bd=0,anchor="e",padx=18,pady=9,font=("Segoe UI",10),cursor="hand2");b.pack(fill="x",padx=8,pady=1);self.buttons[key]=b
        self.content=tk.Frame(body,bg=BG);self.content.pack(side="left",fill="both",expand=True);self.pages={}
        for args in [("dashboard","لوحة المعلومات"),("system","معلومات النظام"),("processes","العمليات"),("storage","التخزين"),("network","الشبكة"),("security","الأمان"),("maintenance","الصيانة والإصلاح"),("services","خدمات Windows"),("startup","بدء التشغيل"),("commands","مركز الأوامر"),("reports","التقارير")]:self.page(*args)
        self._dashboard_controls();self._system_controls();self._process_controls();self._storage_controls();self._network_controls();self._security_controls();self._maintenance_controls();self._service_controls();self._startup_controls();self._command_controls();self._report_controls()
    def page(self,key,title):
        f=tk.Frame(self.content,bg=BG);self.pages[key]=f;tk.Label(f,text=title,bg=BG,fg="white",font=("Segoe UI",18,"bold"),anchor="e").pack(fill="x",padx=24,pady=(22,14));return f
    def show(self,key):
        for f in self.pages.values():f.pack_forget()
        self.pages[key].pack(fill="both",expand=True)
        for k,b in self.buttons.items():b.configure(bg=ACCENT if k==key else PANEL)
        self.status.configure(text=self.buttons[key].cget("text"))
    def card(self,parent,title,col,row):
        c=tk.Frame(parent,bg=PANEL,highlightthickness=1,highlightbackground=PANEL2);c.grid(row=row,column=col,sticky="nsew",padx=6,pady=6);tk.Label(c,text=title,bg=PANEL,fg=MUTED,font=("Segoe UI",10)).pack(fill="x",padx=14,pady=(12,2));v=tk.Label(c,text="—",bg=PANEL,fg=TEXT,font=("Segoe UI",20,"bold"));v.pack(fill="x",padx=14,pady=(0,12));return v
    def _dashboard_controls(self):
        f=self.pages["dashboard"]
        for i in range(3):f.grid_columnconfigure(i,weight=1)
        self.dc=self.card(f,"المعالج",0,0);self.dr=self.card(f,"الذاكرة",1,0);self.dd=self.card(f,"القرص",2,0);self.dp=self.card(f,"العمليات",0,1);self.du=self.card(f,"مدة التشغيل",1,1);self.da=self.card(f,"صلاحيات المسؤول",2,1)
        box=tk.Frame(f,bg=PANEL);box.grid(row=2,column=0,columnspan=3,sticky="ew",padx=6,pady=8);self.health=tk.Label(box,text="جاري القراءة...",bg=PANEL,fg="#93c5fd",font=("Segoe UI",12),anchor="e");self.health.pack(fill="x",padx=16,pady=16);tk.Button(box,text="فحص صحة النظام",command=self.health_check,bg=ACCENT,fg="white",relief="flat",padx=18,pady=8).pack(anchor="e",padx=16,pady=(0,16))
    def _system_controls(self):
        f=self.pages["system"];self.system=self.textbox(f);tk.Button(f,text="تحديث",command=self.refresh_system,bg=ACCENT,fg="white",relief="flat",padx=18,pady=8).pack(anchor="e",padx=24,pady=5)
    def _process_controls(self):
        f=self.pages["processes"];self.proc=self.tree(f,("pid","name","cpu","ram"),("PID","العملية","CPU %","RAM %"));tk.Button(f,text="تحديث العمليات",command=self.refresh_processes,bg=ACCENT,fg="white",relief="flat",padx=18,pady=8).pack(anchor="e",padx=24,pady=5)
    def _storage_controls(self):
        f=self.pages["storage"];self.storage=self.textbox(f);tk.Button(f,text="فحص الأقراص",command=self.refresh_storage,bg=ACCENT,fg="white",relief="flat",padx=18,pady=8).pack(anchor="e",padx=24,pady=5)
    def _network_controls(self):
        f=self.pages["network"];self.network=self.textbox(f);tk.Button(f,text="فحص الشبكة",command=self.refresh_network,bg=ACCENT,fg="white",relief="flat",padx=18,pady=8).pack(anchor="e",padx=24,pady=5)
    def _security_controls(self):
        f=self.pages["security"];self.security=self.textbox(f);tk.Button(f,text="فحص الأمان",command=self.refresh_security,bg=ACCENT,fg="white",relief="flat",padx=18,pady=8).pack(anchor="e",padx=24,pady=5)
    def _maintenance_controls(self):
        f=self.pages["maintenance"];acts=[("تنظيف الملفات المؤقتة",self.clean_temp),("فحص ملفات Windows — SFC",lambda:self.command(["sfc","/scannow"])),("إصلاح Windows — DISM",lambda:self.command(["DISM","/Online","/Cleanup-Image","/RestoreHealth"])),("فحص القرص — CHKDSK",lambda:self.command(["chkdsk","C:","/scan"])),("تفريغ DNS",lambda:self.command(["ipconfig","/flushdns"])),("إعادة ضبط Winsock",lambda:self.command(["netsh","winsock","reset"]))]
        for title,fn in acts:tk.Button(f,text=title,command=fn,bg=PANEL2,fg=TEXT,activebackground=ACCENT,activeforeground="white",relief="flat",anchor="e",padx=18,pady=11,font=("Segoe UI",10)).pack(fill="x",padx=24,pady=4)
        tk.Label(f,text=("تشغيل كمسؤول: نعم" if is_admin() else "تنبيه: شغّل الأداة كمسؤول لتنفيذ إصلاحات Windows."),bg=BG,fg=("#86efac" if is_admin() else WARN),font=("Segoe UI",10)).pack(anchor="e",padx=24,pady=10)
    def _service_controls(self):
        f=self.pages["services"];self.services=self.textbox(f,("Consolas",9));tk.Button(f,text="عرض الخدمات",command=self.refresh_services,bg=ACCENT,fg="white",relief="flat",padx=18,pady=8).pack(anchor="e",padx=24,pady=5)
    def _startup_controls(self):
        f=self.pages["startup"];self.startup=self.textbox(f,("Consolas",9));tk.Button(f,text="فحص بدء التشغيل",command=self.refresh_startup,bg=ACCENT,fg="white",relief="flat",padx=18,pady=8).pack(anchor="e",padx=24,pady=5)
    def _command_controls(self):
        f=self.pages["commands"];self.cmd_entry=tk.Entry(f,bg=PANEL2,fg=TEXT,insertbackground="white",relief="flat",font=("Consolas",11));self.cmd_entry.pack(fill="x",padx=24,pady=8,ipady=8);tk.Button(f,text="تنفيذ الأمر",command=self.run_custom_command,bg=ACCENT,fg="white",relief="flat",padx=18,pady=8).pack(anchor="e",padx=24,pady=5);self.cmd_output=self.textbox(f,("Consolas",9))
    def _report_controls(self):
        f=self.pages["reports"];self.report=self.textbox(f,("Consolas",9));bar=tk.Frame(f,bg=BG);bar.pack(fill="x",padx=24,pady=5);tk.Button(bar,text="توليد التقرير",command=self.refresh_report,bg=ACCENT,fg="white",relief="flat",padx=18,pady=8).pack(side="right");tk.Button(bar,text="حفظ TXT",command=self.save_txt,bg=PANEL2,fg=TEXT,relief="flat",padx=18,pady=8).pack(side="right",padx=5);tk.Button(bar,text="حفظ JSON",command=self.save_json,bg=PANEL2,fg=TEXT,relief="flat",padx=18,pady=8).pack(side="right")
    def textbox(self,parent,font=("Segoe UI",10)):
        t=tk.Text(parent,bg=PANEL,fg=TEXT,insertbackground="white",relief="flat",wrap="word",font=font);t.pack(fill="both",expand=True,padx=24,pady=6);return t
    def tree(self,parent,cols,heads):
        holder=tk.Frame(parent,bg=BG);holder.pack(fill="both",expand=True,padx=24,pady=6);t=ttk.Treeview(holder,columns=cols,show="headings");[t.heading(c,text=h) for c,h in zip(cols,heads)];[t.column(c,anchor="center",width=150) for c in cols];t.pack(side="left",fill="both",expand=True);sb=ttk.Scrollbar(holder,orient="vertical",command=t.yview);sb.pack(side="right",fill="y");t.configure(yscrollcommand=sb.set);return t
    def _live_refresh(self):self.refresh_dashboard();self.after(3500,self._live_refresh)
    def refresh_dashboard(self):
        try:
            cpu=psutil.cpu_percent(None);ram=psutil.virtual_memory().percent;disk=max((psutil.disk_usage(p.mountpoint).percent for p in psutil.disk_partitions(all=False) if os.path.exists(p.mountpoint)),default=0);self.dc.config(text=f"{cpu:.0f}%");self.dr.config(text=f"{ram:.0f}%");self.dd.config(text=f"{disk:.0f}%");self.dp.config(text=str(len(psutil.pids())));self.du.config(text=self.uptime());self.da.config(text="نعم" if is_admin() else "لا");w=max(cpu,ram,disk);self.health.config(text="الحالة: حرجة" if w>=90 else "الحالة: تحتاج انتباه" if w>=75 else "الحالة: جيدة")
        except Exception as e:self.status.config(text=f"خطأ: {e}")
    def refresh_system(self):
        lines=[f"اسم الجهاز: {socket.gethostname()}",f"النظام: {platform.platform()}",f"إصدار Windows: {platform.version()}",f"المعمارية: {platform.machine()}",f"Python: {platform.python_version()}",f"المعالج: {psutil.cpu_count(logical=False) or 0} أنوية فعلية / {psutil.cpu_count() or 0} منطقية",f"الذاكرة: {psutil.virtual_memory().total/1024**3:.2f} GB",f"الإقلاع: {datetime.fromtimestamp(psutil.boot_time()):%Y-%m-%d %H:%M:%S}",f"صلاحيات المسؤول: {'نعم' if is_admin() else 'لا'}"];self.replace(self.system,"\n".join(lines))
    def refresh_processes(self):
        for x in self.proc.get_children():self.proc.delete(x)
        rows=[]
        for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
            try:rows.append((p.info["pid"],p.info["name"] or "",p.info["cpu_percent"] or 0,p.info["memory_percent"] or 0))
            except (psutil.NoSuchProcess,psutil.AccessDenied):pass
        for r in sorted(rows,key=lambda x:x[2],reverse=True)[:150]:self.proc.insert("", "end", values=(r[0],r[1],f"{r[2]:.1f}",f"{r[3]:.1f}"))
    def refresh_storage(self):
        out=[]
        for p in psutil.disk_partitions(all=False):
            try:u=psutil.disk_usage(p.mountpoint);out.append(f"{p.device}  {u.total/1024**3:.1f} GB | متاح {u.free/1024**3:.1f} GB | مستخدم {u.percent:.1f}%")
            except OSError:pass
        self.replace(self.storage,"\n".join(out) or "لم يتم العثور على أقراص.")
    def refresh_network(self):
        c=psutil.net_io_counters();lines=[f"إرسال: {c.bytes_sent/1024**2:.1f} MB",f"استقبال: {c.bytes_recv/1024**2:.1f} MB",""]
        for name,addrs in psutil.net_if_addrs().items():lines.append(name+":");lines.extend("  "+a.address for a in addrs)
        self.replace(self.network,"\n".join(lines))
    def refresh_security(self):
        lines=[f"صلاحيات المسؤول: {'نعم' if is_admin() else 'لا'}"]
        if wmi:
            try:
                c=wmi.WMI()
                for av in c.query("SELECT displayName, productState FROM AntiVirusProduct"):lines.append(f"مكافح الفيروسات: {av.displayName} | الحالة: {av.productState}")
            except Exception as e:lines.append(f"تعذر قراءة WMI للأمان: {e}")
        else:lines.append("WMI غير متاح؛ تم استخدام الموارد الأساسية فقط.")
        self.replace(self.security,"\n".join(lines))
    def refresh_services(self):self._async_command(["sc","query","type=","service","state=","all"],self.services,20)
    def refresh_startup(self):self._async_command(["reg","query",r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"],self.startup,15)
    def command(self,cmd):
        if not messagebox.askyesno("تأكيد","سيتم تنفيذ عملية صيانة في Windows. المتابعة؟"):return
        self.status.config(text="جاري تنفيذ العملية...");self._async_command(cmd,None,900,True)
    def run_custom_command(self):
        raw=self.cmd_entry.get().strip()
        if raw and messagebox.askyesno("تأكيد","تنفيذ الأمر كما كُتب؟"):self._async_custom(raw)
    def _async_custom(self,raw):
        def work():
            try:code,out=run_native(["cmd","/c",raw]);self.after(0,lambda:self.replace(self.cmd_output,f"Exit code: {code}\n\n{out}"))
            except Exception as e:self.after(0,lambda:self.replace(self.cmd_output,str(e)))
        threading.Thread(target=work,daemon=True).start()
    def _async_command(self,cmd,target,timeout,show_window=False):
        def work():
            try:code,out=run_native(cmd,timeout);text=f"Exit code: {code}\n\n{out}";self.after(0,lambda:self._command_done(target,text,show_window))
            except Exception as e:self.after(0,lambda:self._command_done(target,str(e),show_window))
        threading.Thread(target=work,daemon=True).start()
    def _command_done(self,target,text,show_window):
        self.status.config(text="اكتملت العملية")
        if target is not None:self.replace(target,text)
        elif show_window:
            win=tk.Toplevel(self);win.title("نتيجة العملية");win.geometry("900x560");t=self.textbox(win,("Consolas",9));self.replace(t,text)
    def health_check(self):
        self.status.config(text="جاري فحص الصحة...")
        def work():
            cpu=psutil.cpu_percent(interval=1);ram=psutil.virtual_memory().percent;disk=max((psutil.disk_usage(p.mountpoint).percent for p in psutil.disk_partitions(all=False) if os.path.exists(p.mountpoint)),default=0);w=max(cpu,ram,disk);msg="الحالة: حرجة" if w>=90 else "الحالة: تحتاج انتباه" if w>=75 else "الحالة: جيدة";self.after(0,lambda:(self.health.config(text=f"{msg} — CPU {cpu:.0f}% | RAM {ram:.0f}% | Disk {disk:.0f}%"),self.status.config(text="اكتمل الفحص")))
        threading.Thread(target=work,daemon=True).start()
    def clean_temp(self):
        if not messagebox.askyesno("تنظيف","حذف الملفات المؤقتة للمستخدم الحالي؟"):return
        temp=os.environ.get("TEMP") or os.environ.get("TMP");deleted=0
        if temp and os.path.isdir(temp):
            for root,dirs,files in os.walk(temp,topdown=False):
                for name in files:
                    try:os.remove(os.path.join(root,name));deleted+=1
                    except OSError:pass
                for name in dirs:
                    try:os.rmdir(os.path.join(root,name))
                    except OSError:pass
        messagebox.showinfo("التنظيف",f"تم حذف {deleted} ملف تقريبًا.")
    def refresh_report(self):
        data={"timestamp":datetime.now().isoformat(timespec="seconds"),"computer":socket.gethostname(),"platform":platform.platform(),"windows":platform.version(),"python":platform.python_version(),"cpu_percent":psutil.cpu_percent(None),"memory_percent":psutil.virtual_memory().percent,"process_count":len(psutil.pids()),"admin":is_admin(),"disks":[]}
        for p in psutil.disk_partitions(all=False):
            try:u=psutil.disk_usage(p.mountpoint);data["disks"].append({"device":p.device,"total_gb":round(u.total/1024**3,2),"free_gb":round(u.free/1024**3,2),"used_percent":u.percent})
            except OSError:pass
        self.report_data=data;self.replace(self.report,json.dumps(data,ensure_ascii=False,indent=2))
    def save_txt(self):
        if not hasattr(self,"report_data"):self.refresh_report()
        path=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text","*.txt")]);
        if path:Path(path).write_text(self.report.get("1.0","end"),encoding="utf-8");messagebox.showinfo("التقرير","تم حفظ التقرير.")
    def save_json(self):
        if not hasattr(self,"report_data"):self.refresh_report()
        path=filedialog.asksaveasfilename(defaultextension=".json",filetypes=[("JSON","*.json")]);
        if path:Path(path).write_text(json.dumps(self.report_data,ensure_ascii=False,indent=2),encoding="utf-8");messagebox.showinfo("التقرير","تم حفظ JSON.")
    def replace(self,w,text):w.delete("1.0","end");w.insert("end",text)
    @staticmethod
    def uptime():
        sec=max(0,int(datetime.now().timestamp()-psutil.boot_time()));d,sec=divmod(sec,86400);h,sec=divmod(sec,3600);return f"{d} يوم، {h} ساعة"
def run():App().mainloop()
