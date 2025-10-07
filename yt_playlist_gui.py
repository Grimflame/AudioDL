
"""
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


def download_audio(video_id: str, out_dir: Path, q: queue.Queue, audio_format: str):
    cmd = [
        str(YTDLP_EXE),
        "-x", "--audio-format", audio_format,
        "--embed-thumbnail", "--add-metadata",
        "--ffmpeg-location", str(FFMPEG_EXE),
        "-P", str(out_dir),
        f"https://www.youtube.com/watch?v={video_id}",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    pattern = re.compile(r"[download]\s*(?P<pct>[0-9.]+)%.*?at\s*(?P<spd>\S+)\s*ETA\s*(?P<eta>[0-9:]+)")
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
        self.ttk_theme_var = tk.StringVar(value=self.settings.get("ttk_theme", "clam")) # Changed default to "clam"
        self.format_var = tk.StringVar(value="aac") # NEW
        self.selected_count = tk.IntVar(value=0)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._filter_list)

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
        self.settings["ttk_theme"] = self.ttk_theme_var.get() # NEW
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
        themem.add_separator()
        # Add ttk themes
        for th in ttk.Style().theme_names():
            themem.add_radiobutton(label=th.capitalize(), variable=self.ttk_theme_var, value=th, command=self._apply_theme)
        menu.add_cascade(label="Theme", menu=themem)
        self.config(menu=menu)

    # ---------------- HEADER ----------------
    def _build_header(self):
        frame = ttk.Frame(self)
        frame.pack(fill="x", padx=10, pady=5)
        ttk.Entry(frame, textvariable=self.url_var).pack(side="left", expand=True, fill="x", padx=(0,5))
        ttk.Button(frame, text="Analyze", command=self.analyze).pack(side="left")
        ttk.Label(frame, text="Search:").pack(side="left", padx=(15,5))
        ttk.Entry(frame, textvariable=self.search_var, width=30).pack(side="left", fill="x", padx=(0,5))
        ttk.Label(frame, text="Format:").pack(side="left", padx=(15,5))
        format_options = ["aac", "mp3", "flac", "wav"]
        ttk.Combobox(frame, textvariable=self.format_var, values=format_options, width=8).pack(side="left", padx=(0,5))
        ttk.Label(frame, text="Output:").pack(side="left", padx=(15,5))
        ttk.Entry(frame, textvariable=self.out_dir_var, width=30).pack(side="left", fill="x", padx=(0,5))
        ttk.Button(frame, text="…", width=3, command=self.open_select_out).pack(side="left")

    # ---------------- CHECKLIST ----------------
    def _build_checklist(self):
        wrap = ttk.Frame(self)
        wrap.pack(expand=True, fill="both", padx=10, pady=5)
        self.canvas = tk.Canvas(wrap)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.canvas.yview, style="Vertical.TScrollbar")
        self.list_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0,0), window=self.list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=vsb.set)
        self.list_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._bind_scroll(self.canvas)
        self._bind_scroll(self.list_frame)

        ctrl = ttk.Frame(self)
        ctrl.pack(fill="x", padx=10)
        ttk.Button(ctrl, text="Select All", command=self.select_all).pack(side="left")
        ttk.Button(ctrl, text="Deselect All", command=self.deselect_all).pack(side="left", padx=5)
        ttk.Button(ctrl, text="Refresh", command=self._refresh_downloaded_status).pack(side="left", padx=5)
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
        # Apply ttk theme first
        selected_ttk_theme = self.ttk_theme_var.get()
        style = ttk.Style()
        style.theme_use(selected_ttk_theme)

        dark = self.theme_var.get() == "dark"
        # More modern colors
        bg = "#282c34" if dark else "#ffffff" # Darker background for dark, pure white for light
        fg = "#abb2bf" if dark else "#333333" # Lighter text for dark, darker for light
        accent_color = "#61afef" if dark else "#007bff" # A blue accent

        # Highlight colors
        self.selected_highlight_color = "#a8e6cf" if dark else "#d4edda" # Green for selected
        self.downloaded_highlight_color = "#ffd3b6" if dark else "#ffeeba" # Orange for downloaded

        self.configure(bg=bg)

        # Configure general styles
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg, font=("Segoe UI", 10)) # Changed font
        style.configure("TCheckbutton", background=bg, foreground=fg, font=("Segoe UI", 10)) # Changed font
        style.configure("TButton", padding=(8, 5), font=("Segoe UI", 10, "bold"),
                        background=accent_color, foreground="#ffffff") # Changed font, padding, colors
        style.map("TButton",
                  background=[("active", accent_color)],
                  foreground=[("active", "#ffffff")])

        # Styles for list items
        style.configure("Downloaded.TFrame", background=self.downloaded_highlight_color)
        style.configure("Selected.TFrame", background=self.selected_highlight_color)
        style.configure("Downloaded.TCheckbutton", background=self.downloaded_highlight_color, foreground=fg, font=("Segoe UI", 10))
        style.configure("Selected.TCheckbutton", background=self.selected_highlight_color, foreground=fg, font=("Segoe UI", 10))

        self.canvas.configure(background=bg)

        # Scrollbar styling
        scrollbar_bg = "#44475a" if dark else "#e0e0e0"
        scrollbar_trough = "#343746" if dark else "#f0f0f0"
        style.configure("Vertical.TScrollbar", background=scrollbar_bg, troughcolor=scrollbar_trough, bordercolor=scrollbar_bg, arrowcolor=fg)
        style.map("Vertical.TScrollbar",
                  background=[("active", scrollbar_bg)],
                  troughcolor=[("active", scrollbar_trough)])

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
            self.entries = entries
            self.queue.put(("populate", None))
        except Exception as e:
            self.queue.put(("error", str(e)))

    def _filter_list(self, *args):
        search_term = self.search_var.get().lower()
        if search_term:
            filtered_entries = [
                e for e in self.entries
                if search_term in e.get("title", "").lower()
            ]
        else:
            filtered_entries = self.entries
        self._populate_list(filtered_entries)

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
        selected_format = self.format_var.get()
        for vid in ids:
            download_audio(vid, out, self.queue, selected_format)
        self.queue.put(("finished", str(out)))

    # ---------------- QUEUE POLLING ----------------
    def _poll_queue(self):
        try:
            msg, *payload = self.queue.get_nowait()
            if msg == "populate":
                self._populate_list()
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
                if messagebox.askyesno("Finished", f"Saved to:\n{out}\nOpen folder?"):
                    os.startfile(out)
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

    # ---------------- POPULATE LIST ----------------
    def _populate_list(self, entries_to_populate: list[dict] = None):
        if entries_to_populate is None:
            entries_to_populate = self.entries

        for w in self.list_frame.winfo_children():
            w.destroy()
        self.check_vars = []
        out = Path(self.out_dir_var.get())
        existing = set()
        if out.exists():
            for f in out.iterdir():
                if f.suffix == ".m4a":
                    m = re.search(r"[-_ ]?\[?([A-Za-z0-9_-]{11})\]?\.m4a$", f.name)
                    if m:
                        existing.add(m.group(1))
        for e in entries_to_populate:
            vid = e.get("id")
            title = e.get("title","(untitled)")
            dur = fmt_dur(e.get("duration"))
            done = vid in existing
            var = tk.IntVar(value=0 if done else 1)

            item_frame = ttk.Frame(self.list_frame) # NEW FRAME FOR HIGHLIGHT
            item_frame.pack(anchor="w", fill="x", pady=2)

            text = f"{title} • {dur}" + (" (downloaded)" if done else "")
            cb = ttk.Checkbutton(item_frame, text=text, variable=var, command=lambda v=var, f=item_frame: self._on_checkbutton_toggle(v, f)) # MODIFIED COMMAND

            # Apply initial highlight color
            if done:
                item_frame.configure(style="Downloaded.TFrame")
                cb.configure(style="Downloaded.TCheckbutton", state="disabled")
            elif var.get(): # If initially selected
                item_frame.configure(style="Selected.TFrame")
                cb.configure(style="Selected.TCheckbutton")

            cb.pack(side="left", fill="x", expand=True) # Pack checkbox inside its frame
            self._bind_scroll(item_frame) # Bind scroll to the frame
            self.check_vars.append((var, vid))
        self._update_selected_count()
        self.progress.stop()
        self.status_lbl.configure(text=f"Playlist: {len(entries_to_populate)} videos loaded.")
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

    # ---------------- HELPERS ----------------
    def _on_checkbutton_toggle(self, var, item_frame):
        self._update_selected_count()
        cb = item_frame.winfo_children()[0]
        if var.get():
            item_frame.configure(style="Selected.TFrame")
            cb.configure(style="Selected.TCheckbutton")
        else:
            item_frame.configure(style="TFrame")
            cb.configure(style="TCheckbutton")

    def _update_selected_count(self):
        self.selected_count.set(sum(v.get() for v, _ in self.check_vars))

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

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # ---------------- HELPERS ----------------
    def _update_selected_count(self):
        self.selected_count.set(sum(v.get() for v, _ in self.check_vars))

    def select_all(self):
        for v,_ in self.check_vars:
            v.set(1)
        self._update_selected_count()

    def deselect_all(self):
        for v,_ in self.check_vars:
            v.set(0)
        self._update_selected_count()

    def open_out_dir(self):
        try:
            os.startfile(self.out_dir_var.get())
        except Exception as e:
            messagebox.showerror("Error", f"Could not open folder:\n{e}")

    def open_select_out(self):
        new = filedialog.askdirectory(initialdir=self.out_dir_var.get())
        if new:
            self.out_dir_var.set(new)

    def _refresh_downloaded_status(self):
        self.status_lbl.configure(text="Refreshing downloaded status...")
        self.progress.configure(mode="indeterminate"); self.progress.start()
        self._populate_list()
        self.progress.stop()
        self.status_lbl.configure(text="Ready.")

    def _toggle_ui_state(self, parent, state):
        for child in parent.winfo_children():
            if isinstance(child, (ttk.Button, ttk.Entry)):
                child.state([state])
            if child.winfo_children():
                self._toggle_ui_state(child, state)

    def _lock_ui(self):
        self._toggle_ui_state(self, 'disabled')

    def _unlock_ui(self):
        self._toggle_ui_state(self, '!disabled')

# ------------------------------------------------------------------
if __name__ == "__main__":
    DEFAULT_OUT_DIR.mkdir(exist_ok=True)
    app = App()
    app.mainloop()
