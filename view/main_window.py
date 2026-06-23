import tkinter as tk
from tkinter import ttk, scrolledtext
import datetime

from view.theme import (
    BG, PANEL, BORDER, ACCENT, ACCENT2, FG, FG_DIM,
    SUCCESS, WARNING, FONT_UI, FONT_HEAD, FONT_BIG, FONT_MONO
)
from view.aliquota_panel import AliquotaPanel


class MainWindow:
    def __init__(self, root: tk.Tk, controller):
        self.root = root
        self.controller = controller

        self.root.title("ImportadorSistemaDatha")
        self.root.geometry("1100x780")
        self.root.minsize(980, 700)
        self.root.configure(bg=BG)

        self._build()

    # ─────────────────────────────────────────
    # Layout
    # ─────────────────────────────────────────
    def _build(self):
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=10)
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        right = tk.Frame(body, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")

        self._build_firebird_panel(left)
        self._build_postgres_panel(left)
        self._build_test_button(left)
        self._build_aliquota_panel(left)
        self._build_import_panel(left)
        self._build_log_panel(right)

    def _card(self, parent, title) -> tk.Frame:
        outer = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        outer.pack(fill="x", pady=(0, 10))
        tk.Label(outer, text=title, bg=PANEL, fg=ACCENT,
                 font=FONT_HEAD, anchor="w").pack(fill="x", padx=12, pady=(10, 6))
        tk.Frame(outer, bg=BORDER, height=1).pack(fill="x", padx=12)
        inner = tk.Frame(outer, bg=PANEL)
        inner.pack(fill="x", padx=12, pady=10)
        return inner

    def _entry_row(self, parent, label: str, row: int, show=None) -> tk.StringVar:
        tk.Label(parent, text=label, bg=PANEL, fg=FG_DIM,
                 font=FONT_UI, anchor="w").grid(row=row, column=0, sticky="w", pady=3)
        var = tk.StringVar()
        e = tk.Entry(
            parent, textvariable=var,
            bg=BG, fg=FG, insertbackground=FG,
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
            font=FONT_UI, show=show or ""
        )
        e.grid(row=row, column=1, sticky="ew", padx=(8, 0), pady=3, ipady=4)
        parent.columnconfigure(1, weight=1)
        return var

    def _build_firebird_panel(self, parent):
        card = self._card(parent, "Config Firebird")
        self.fb_host = self._entry_row(card, "Host",     0)
        self.fb_port = self._entry_row(card, "Port",     1)
        self.fb_db   = self._entry_row(card, "Database", 2)
        self.fb_user = self._entry_row(card, "User",     3)
        self.fb_pass = self._entry_row(card, "Password", 4, show="•")
        self.fb_host.set("localhost")
        self.fb_port.set("3050")
        self.fb_user.set("SYSDBA")
        self.fb_pass.set("masterkey")

    def _build_postgres_panel(self, parent):
        card = self._card(parent, "Config PostgreSQL")
        self.pg_host = self._entry_row(card, "Host",     0)
        self.pg_port = self._entry_row(card, "Port",     1)
        self.pg_db   = self._entry_row(card, "Database", 2)
        self.pg_user = self._entry_row(card, "User",     3)
        self.pg_pass = self._entry_row(card, "Password", 4, show="•")
        self.pg_host.set("localhost")
        self.pg_port.set("5432")
        self.pg_user.set("postgres")
        self.pg_pass.set("@skydiver2442!")

    def _build_test_button(self, parent):
        tk.Button(
            parent, text="Testar conexão",
            command=self.controller.on_test_connections,
            bg=ACCENT, fg="white", activebackground="#6A5AE0",
            font=FONT_UI, relief="flat", cursor="hand2",
            padx=12, pady=7
        ).pack(fill="x", pady=(0, 10))

    def _build_aliquota_panel(self, parent):
        self.aliquota_panel = AliquotaPanel(
            parent,
            on_mapping_changed=self.controller.on_mapping_changed
        )
        self.aliquota_panel.pack(fill="x", pady=(0, 10))

    def _build_import_panel(self, parent):
        card = self._card(parent, "Importar")
        self.btn_import = tk.Button(
            card, text="Importar novos",
            command=self.controller.on_start_import,
            bg="#444460", fg=FG_DIM,
            activebackground=SUCCESS,
            font=FONT_HEAD, relief="flat",
            cursor="hand2", padx=12, pady=10,
            state="disabled"
        )
        self.btn_import.pack(fill="x")

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            card, variable=self.progress_var,
            maximum=100, mode="determinate"
        )
        self.progress.pack(fill="x", pady=(8, 0))
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TProgressbar", troughcolor=BG, background=ACCENT2, thickness=6)

    def _build_log_panel(self, parent):
        hdr = tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Log de execução", bg=PANEL, fg=ACCENT,
                 font=FONT_HEAD, anchor="w").pack(side="left", padx=12, pady=10)
        tk.Button(hdr, text="Limpar", command=self.clear_log,
                  bg=PANEL, fg=FG_DIM, relief="flat",
                  font=FONT_UI, cursor="hand2").pack(side="right", padx=8)

        self.log_box = scrolledtext.ScrolledText(
            parent, bg="#0D0D1A", fg=FG, font=FONT_MONO,
            relief="flat", bd=0, wrap="word",
            insertbackground=FG, state="disabled"
        )
        self.log_box.pack(fill="both", expand=True, pady=(2, 0))
        self.log_box.tag_config("ok",   foreground=SUCCESS)
        self.log_box.tag_config("err",  foreground="#FF6B6B")
        self.log_box.tag_config("warn", foreground=WARNING)
        self.log_box.tag_config("info", foreground=ACCENT2)
        self.log_box.tag_config("dim",  foreground=FG_DIM)

    # ─────────────────────────────────────────
    # Public API used by controller
    # ─────────────────────────────────────────
    def get_fb_credentials(self) -> dict:
        return {
            "host":     self.fb_host.get().strip(),
            "port":     self.fb_port.get().strip(),
            "database": self.fb_db.get().strip(),
            "user":     self.fb_user.get().strip(),
            "password": self.fb_pass.get(),
        }

    def get_pg_credentials(self) -> dict:
        return {
            "host":     self.pg_host.get().strip(),
            "port":     self.pg_port.get().strip(),
            "database": self.pg_db.get().strip(),
            "user":     self.pg_user.get().strip(),
            "password": self.pg_pass.get(),
        }

    def load_aliquotas(self, fb_list: list[str], pg_list: list[dict]):
        self.aliquota_panel.load(fb_list, pg_list)

    def set_import_enabled(self, enabled: bool):
        if enabled:
            self.btn_import.config(state="normal", bg=ACCENT2,
                                   fg="#0D0D1A", activebackground=SUCCESS)
        else:
            self.btn_import.config(state="disabled", bg="#444460", fg=FG_DIM)

    def set_progress(self, pct: float):
        self.progress_var.set(pct)

    def log(self, msg: str, tag: str = ""):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{ts}] {msg}\n", tag)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")
