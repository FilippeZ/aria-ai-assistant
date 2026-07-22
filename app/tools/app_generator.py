#!/usr/bin/env python3
"""
Autonomous PC Desktop Application Generator & Launcher for Aria Hybrid Assistant.
Generates and launches custom GUI productivity applications for local files and system tasks.
"""

import sys
import os
import subprocess
from pathlib import Path

def generate_jetson_file_manager_gui() -> str:
    """Generate and launch a standalone Jetson File & Knowledge GUI App."""
    script_path = Path("/tmp/jetson_file_dashboard.py")
    
    code = '''#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

class JetsonFileDashboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⚡ Jetson Orin Nano - File & Knowledge Dashboard")
        self.geometry("780x560")
        self.configure(bg="#1e1e2e")
        
        # Header Label
        header = tk.Label(
            self,
            text="🤖 Aria PC File Intelligence & Storage Dashboard",
            font=("Helvetica", 16, "bold"),
            bg="#313244",
            fg="#cdd6f4",
            pady=12
        )
        header.pack(fill="x")
        
        # Main Frame
        main_frame = tk.Frame(self, bg="#1e1e2e", padx=15, pady=15)
        main_frame.pack(fill="both", expand=True)
        
        # Disk Stats Section
        stats_frame = tk.LabelFrame(main_frame, text=" 📊 Storage & Disk Stats ", bg="#1e1e2e", fg="#a6e3a1", font=("Helvetica", 11, "bold"), padx=10, pady=10)
        stats_frame.pack(fill="x", pady=5)
        
        total, used, free = shutil.disk_usage("/")
        disk_info = f"Root Drive (/): Total: {total // (2**30)} GB  |  Used: {used // (2**30)} GB  |  Free: {free // (2**30)} GB"
        tk.Label(stats_frame, text=disk_info, bg="#1e1e2e", fg="#cdd6f4", font=("Helvetica", 10)).pack(anchor="w")
        
        # File List Section
        files_frame = tk.LabelFrame(main_frame, text=" 📁 Local Knowledge Base & Assistant Documents ", bg="#1e1e2e", fg="#89b4fa", font=("Helvetica", 11, "bold"), padx=10, pady=10)
        files_frame.pack(fill="both", expand=True, pady=10)
        
        # Treeview list for files
        columns = ("name", "size", "path")
        self.tree = ttk.Treeview(files_frame, columns=columns, show="headings", height=8)
        self.tree.heading("name", text="File Name")
        self.tree.heading("size", text="Size")
        self.tree.heading("path", text="Absolute Path")
        self.tree.column("name", width=200)
        self.tree.column("size", width=100)
        self.tree.column("path", width=400)
        self.tree.pack(fill="both", expand=True, side="left")
        
        scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        
        # Button Action Bar
        btn_frame = tk.Frame(main_frame, bg="#1e1e2e")
        btn_frame.pack(fill="x", pady=5)
        
        refresh_btn = tk.Button(btn_frame, text="🔄 Refresh Files", bg="#89b4fa", fg="#11111b", font=("Helvetica", 10, "bold"), command=self.load_files, padx=10)
        refresh_btn.pack(side="left", padx=5)
        
        open_btn = tk.Button(btn_frame, text="👁️ Open Selected File", bg="#a6e3a1", fg="#11111b", font=("Helvetica", 10, "bold"), command=self.open_selected, padx=10)
        open_btn.pack(side="left", padx=5)
        
        close_btn = tk.Button(btn_frame, text="❌ Close Dashboard", bg="#f38ba8", fg="#11111b", font=("Helvetica", 10, "bold"), command=self.destroy, padx=10)
        close_btn.pack(side="right", padx=5)
        
        self.load_files()
        
    def load_files(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        base_dir = Path(__file__).parent.parent.parent
        kb_dir = base_dir / "knowledge_base"
        if kb_dir.exists():
            for f in kb_dir.glob("*"):
                if f.is_file():
                    size = f"{f.stat().st_size / 1024:.1f} KB"
                    self.tree.insert("", "end", values=(f.name, size, str(f)))
                    
        proj_dir = base_dir
        for f in proj_dir.glob("*.py"):
            size = f"{f.stat().st_size / 1024:.1f} KB"
            self.tree.insert("", "end", values=(f.name, size, str(f)))
            
    def open_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a file from the list first.")
            return
        item = self.tree.item(selected[0])
        file_path = item["values"][2]
        try:
            subprocess.Popen(["xdg-open", file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")

if __name__ == "__main__":
    app = JetsonFileDashboard()
    app.mainloop()
'''
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)
    
    os.chmod(script_path, 0o755)
    
    # Launch GUI using environment python
    base_dir = Path(__file__).parent.parent.parent
    venv_py = str(base_dir / "venv" / "bin" / "python")
    subprocess.Popen([venv_py, str(script_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return f"Created custom GUI application at '{script_path}' and launched it on your PC desktop!"

if __name__ == "__main__":
    print(generate_jetson_file_manager_gui())
