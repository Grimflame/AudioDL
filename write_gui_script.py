# write_gui_script.py

file_content = """
Fixed and cleaned version of YouTube Playlist Audio Downloader GUI
- Removed duplicate methods and orphaned code
- Corrected `_poll_queue` indentation and logic
- Fixed application entry-point
- Ensured all widgets and vars initialized properly
- Maintains all QOL features (scroll, progress, dedupe, themes, embed thumbnail)
"""

import os
import re
import json
import queue
import threading
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------
BASE_DIR        = Path(__file__).resolve().parent
YTDLP_EXE       = BASE_DIR / "yt-dlp.exe"
FFMPEG_EXE      = BASE_DIR / "ffmpeg" / "bin" / "ffmpeg.exe"
DEFAULT_OUT_DIR = BASE_DIR / "Musiques"
SETTINGS_FILE   = BASE_DIR / "settings.json"

# ------------------------------------------------------------------
# UTILITIES
# ------------------------------------------------------------------
def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def fetch_playlist(url: str) -> list[dict]:
    res = run([str(YTDLP_EXE), "--flat-playlist", "-J", url])
    if res.returncode != 0:
        raise RuntimeError(res.stderr or "yt-dlp failed to fetch playlist.")
    data = json.loads(res.stdout)
    if "entries" not in data:
        raise RuntimeError("Invalid playlist URL or access denied.")
    return data["entries"]


def fmt_dur(sec: int | None) -> str:
    if sec is None:
        return "?"
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def load_settings() -> dict:
    if SETTINGS_FILE.exists():
        return json.loads(SETTINGS_FILE.read_text())
    return {}


def save_settings(settings: dict):
    SETTINGS_FILE.write_text(json.dumps(settings, indent=2))


def download_audio(video_id: str, out_dir: Path, q: queue.Queue):
    cmd = [
        str(YTDLP_EXE),
        "-x", "--audio-format", "aac",
        "--embed-thumbnail", "--add-metadata",
        "--ffmpeg-location", str(FFMPEG_EXE),
        "-P", str(out_dir),
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    pattern = re.compile(r"[download]\\s*(?P<pct>[0-9.]+)%.*?at\\s*(?P<spd>\S+)\\s*ETA\\s*(?P<eta>[0-9:]+)")
    for line in proc.stdout:
        m = pattern.search(line)
        if m:
            pct = float(m.group("pct"))
            spd = m.group("spd")
            eta = m.group("eta")
            q.put(("progress", pct, spd, eta))
        elif "WARNING: [AtomicParsley]" in line:
            q.put(("warning", line.strip()))
    proc.wait()
    q.put(("done", video_id, proc.returncode == 0))

# ------------------------------------------------------------------
# MAIN APPLICATION CLASS
# ------------------------------------------------------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Playlist Audio DL")
        self.geometry("800x600")

        # Settings and state
        self.settings = load_settings()
        self.url_var = tk.StringVar(value=self.settings.get("last_url", ""))
        self.out_dir_var = tk.StringVar(value=self.settings.get("output_directory", str(DEFAULT_OUT_DIR)))
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "light"))
        self.selected_count = tk.IntVar(value=0)

        self.queue = queue.Queue()
        self.warnings = []
        self.entries = []
        self.check_vars = []

        # Build UI
        self._build_menu()
        self._build_header()
        self._build_checklist()
        self._build_footer()
        self._apply_theme()

        # Bindings
        self.bind_all("<Control-a>", lambda e: self.select_all())
        self.bind_all("<Control-d>", lambda e: self.deselect_all())

        # Poll queue
        self.after(100, self._poll_queue)

        # On close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.settings["last_url"] = self.url_var.get()
        self.settings["output_directory"] = self.out_dir_var.get()
        self.settings["theme"] = self.theme_var.get()
        save_settings(self.settings)
        self.destroy()

    # ---------------- MENU ----------------
    def _build_menu(self):
        menu = tk.Menu(self)
        filem = tk.Menu(menu, tearoff=False)
        filem.add_command(label="Open Output Folder", command=self.open_out_dir)
        filem.add_separator()
        filem.add_command(label="Exit", command=self._on_close)
        menu.add_cascade(label="File", menu=filem)

        themem = tk.Menu(menu, tearoff=False)
        themem.add_radiobutton(label="Light", variable=self.theme_var, value="light", command=self._apply_theme)
        themem.add_radiobutton(label="Dark", variable=self.theme_var, value="dark", command=self._apply_theme)
        menu.add_cascade(label="Theme", menu=themem)
        self.config(menu=menu)

    # ---------------- HEADER ----------------
    def _build_header(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=10, pady=5)
        ttk.Entry(frame, textvariable=self.url_var).pack(side="left", expand=True, fill="x", padx=(0,5))
        ttk.Button(frame, text="Analyze", command=self.analyze).pack(side="left")
        ttk.Label(frame, text="Output:").pack(side="left", padx=(15,5))
        ttk.Entry(frame, textvariable=self.out_dir_var, width=30).pack(side="left", fill="x", padx=(0,5))
        ttk.Button(frame, text="…", width=3, command=self.open_select_out).pack(side="left")

    # ---------------- CHECKLIST ----------------
    def _build_checklist(self):
        wrap = ttk.Frame(self)
        wrap.pack(expand=True, fill="both", padx=10, pady=5)
        self.canvas = tk.Canvas(wrap)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.canvas.yview)
        self.list_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0,0), window=self.list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=vsb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._bind_scroll(self.canvas)
        self._bind_scroll(self.list_frame)

        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", padx=10)
        ttk.Button(ctrl, text="Select All", command=self.select_all).pack(side="left")
        ttk.Button(ctrl, text="Deselect All", command=self.deselect_all).pack(side="left", padx=5)
        ttk.Button(ctrl, text="Download Selected", command=self.download_selected).pack(side="right")

    # ---------------- FOOTER ----------------
    def _build_footer(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=10, pady=(0,10))
        self.progress = ttk.Progressbar(frame, mode="determinate")
        self.progress.pack(fill="x")
        status_frame = ttk.Frame(frame)
        status_frame.pack(fill="x", pady=(5,0))
        self.status_lbl = ttk.Label(status_frame, text="Ready.")
        self.status_lbl.pack(side="left", fill="x", expand=True)
        self.details_lbl = ttk.Label(status_frame, text="")
        self.details_lbl.pack(side="right")
        ttk.Label(status_frame, text="Selected:").pack(side="right", padx=(5,0))
        ttk.Label(status_frame, textvariable=self.selected_count).pack(side="right")

    # ---------------- THEME ----------------
    def _apply_theme(self):
        dark = self.theme_var.get() == "dark"
        bg = "#333" if dark else "#f0f0f0"
        fg = "#f0f0f0" if dark else "#000"
        self.configure(bg=bg)
        style = ttk.Style()
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TCheckbutton", background=bg, foreground=fg)
        style.configure("TButton", padding=(5,3))
        self.canvas.configure(background=bg)

    # ---------------- ANALYZE ----------------
    def analyze(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showinfo("Info", "Please paste a playlist URL.")
            return
        self.settings["last_url"] = url
        save_settings(self.settings)
        self._lock_ui()
        self.status_lbl.configure(text="Analyzing playlist...")
        self.progress.configure(mode="indeterminate"); self.progress.start()
        threading.Thread(target=self._analyze_worker, args=(url,), daemon=True).start()

    def _analyze_worker(self, url: str):
        try:
            entries = fetch_playlist(url)
            self.queue.put(("populate", entries))
        except Exception as e:
            self.queue.put(("error", str(e)))

    # ---------------- DOWNLOAD ----------------
    def download_selected(self):
        selected = [vid for var,vid in self.check_vars if var.get()]
        if not selected:
            messagebox.showinfo("Info", "No videos selected.")
            return
        out = Path(self.out_dir_var.get())
        out.mkdir(parents=True, exist_ok=True)
        self._lock_ui()
        self.status_lbl.configure(text="Starting downloads...")
        self.progress.configure(mode="determinate", value=0, maximum=len(selected))
        self.details_lbl.configure(text="")
        threading.Thread(target=self._download_worker, args=(selected, out), daemon=True).start()

    def _download_worker(self, ids: list[str], out: Path):
        for vid in ids:
            download_audio(vid, out, self.queue)
        self.queue.put(("finished", str(out)))

    # ---------------- QUEUE POLLING ----------------
    def _poll_queue(self):
        try:
            while True:
                msg, *payload = self.queue.get_nowait()
                if msg == "populate":
                    self._populate_list(payload[0])
                elif msg == "progress":
                    pct, spd, eta = payload
                    self.progress.configure(value=pct)
                    self.details_lbl.configure(text=f"{pct:.1f}% • {spd} • ETA {eta}")
                elif msg == "done":
                    vid, ok = payload
                    self.progress.step(1)
                elif msg == "error":
                    self._unlock_ui()
                    messagebox.showerror("Error", payload[0])
                elif msg == "finished":
                    out = payload[0]
                    self._unlock_ui()
                    self.status_lbl.configure(text="All done.")
                    self.details_lbl.configure(text="")
                    if self.warnings:
                        messagebox.showwarning("Warnings", "\n".join(self.warnings))
                        self.warnings.clear()
                    if messagebox.askyesno("Finished", f"Saved to:\n{out}\nOpen folder?" ):
                        os.startfile(out)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    # ---------------- POPULATE LIST ----------------
    def _populate_list(self, entries: list[dict]):
        for w in self.list_frame.winfo_children():
            w.destroy()
        self.entries = entries
        self.check_vars = []
        out = Path(self.out_dir_var.get())
        existing = set()
        if out.exists():
            for f in out.iterdir():
                if f.suffix == ".m4a":
                    m = re.search(r"([A-Za-z0-9_-]{11})", f.name)
                    if m:
                        existing.add(m.group(1))
        for e in entries:
            vid = e.get("id")
            title = e.get("title","(untitled)")
            dur = fmt_dur(e.get("duration"))
            done = vid in existing
            var = tk.IntVar(value=0 if done else 1)
            text = f"{title} • {dur}" + (" (downloaded)" if done else "")
            cb = ttk.Checkbutton(self.list_frame, text=text, variable=var)
            if done:
                cb.configure(state="disabled")
            cb.pack(anchor="w", fill="x", pady=2)
            self._bind_scroll(cb)
            self.check_vars.append((var, vid))
        self.selected_count.set(sum(v.get() for v,_ in self.check_vars))
        self.progress.stop()
        self.status_lbl.configure(text=f"Playlist: {len(entries)} videos loaded.")
        self._unlock_ui()

    # ---------------- SCROLL BINDING ----------------
    def _on_mousewheel(self, event):
        if os.name == 'nt':
            self.canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
        else:
            if event.num == 4:
                self.canvas.yview_scroll(-1, 'units')
            elif event.num == 5:
                self.canvas.yview_scroll(1, 'units')

    def _bind_scroll(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)

    # ---------------- LOCK/UNLOCK UI ----------------
    def select_all(self):
        for v,_ in self.check_vars:
            v.set(1)
        self.selected_count.set(sum(v.get() for v,_ in self.check_vars))

    def deselect_all(self):
        for v,_ in self.check_vars:
            v.set(0)
        self.selected_count.set(0)

    def open_out_dir(self):
        try:
            os.startfile(self.out_dir_var.get())
        except:
            pass

    def open_select_out(self):
        new = filedialog.askdirectory(initialdir=self.out_dir_var.get())
        if new:
            self.out_dir_var.set(new)

    def _lock_ui(self):
        for w in self.winfo_children():
            if isinstance(w, (ttk.Entry, ttk.Button)):
                w.state(['disabled'])

    def _unlock_ui(self):
        for w in self.winfo_children():
            if isinstance(w, (ttk.Entry, ttk.Button)):
                w.state(['!disabled'])

# ------------------------------------------------------------------
if __name__ == "__main__":
    DEFAULT_OUT_DIR.mkdir(exist_ok=True)
    app = App()
    app.mainloop()
