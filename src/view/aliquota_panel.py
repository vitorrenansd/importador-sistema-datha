import tkinter as tk
from tkinter import ttk

from view.theme import (
    BG, PANEL, BORDER, ACCENT, FG, FG_DIM,
    SUCCESS, WARNING, FONT_UI, FONT_HEAD, FONT_MONO
)


class AliquotaPanel(tk.Frame):
    """
    Panel that renders one dropdown row per distinct CDALIQ found in Firebird.
    Calls on_mapping_complete(complete: bool) whenever the mapping state changes.
    """

    def __init__(self, parent, on_mapping_changed, **kwargs):
        super().__init__(parent, bg=PANEL, **kwargs)
        self._on_mapping_changed = on_mapping_changed
        self._aliq_vars: dict[str, tuple[tk.StringVar, dict]] = {}
        self._mapping: dict[str, int] = {}
        self._pg_options: dict[str, int] = {}

        self._build_header()
        self._build_placeholder()

    # ─────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=PANEL)
        hdr.pack(fill="x", padx=12, pady=(10, 6))
        tk.Label(hdr, text="Associação de Aliquotas", bg=PANEL, fg=ACCENT,
                 font=FONT_HEAD, anchor="w").pack(side="left")
        self.status_label = tk.Label(hdr, text="", bg=PANEL, fg=WARNING, font=FONT_UI)
        self.status_label.pack(side="right")
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=12)

    def _build_placeholder(self):
        self.placeholder = tk.Label(
            self, bg=PANEL, fg=FG_DIM, font=FONT_UI, justify="left",
            text="Conecte as duas bases para associar as aliquotas",
            wraplength=340, anchor="w"
        )
        self.placeholder.pack(padx=12, pady=10, anchor="w")
        self.rows_frame = None

    # ─────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────
    def load(self, fb_cdaliq_list: list[str], pg_aliquotas: list[dict]):
        """Called by controller after both connections succeed."""
        self._mapping.clear()
        self._aliq_vars.clear()

        self._pg_options = {
            f"{r['s_descricao']} (id = {r['i_cod_bs_aliquota_c']})": r["i_cod_bs_aliquota_c"]
            for r in pg_aliquotas
        }
        pg_display = list(self._pg_options.keys())

        if self.placeholder:
            self.placeholder.destroy()
            self.placeholder = None
        if self.rows_frame:
            self.rows_frame.destroy()

        self.rows_frame = tk.Frame(self, bg=PANEL)
        self.rows_frame.pack(fill="x", padx=12, pady=(8, 10))

        # Canvas + scrollbar for many rows
        canvas = tk.Canvas(self.rows_frame, bg=PANEL, highlightthickness=0,
                           height=min(200, len(fb_cdaliq_list) * 42))
        vsb = tk.Scrollbar(self.rows_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=PANEL)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Column headers
        tk.Label(inner, text="CDALIQ (Firebird)", bg=PANEL, fg=FG_DIM,
                 font=FONT_UI, width=18, anchor="w").grid(row=0, column=0, padx=4, pady=2)
        tk.Label(inner, text="Aliquota PostgreSQL", bg=PANEL, fg=FG_DIM,
                 font=FONT_UI, anchor="w").grid(row=0, column=1, padx=4, pady=2, sticky="w")

        for i, cd in enumerate(fb_cdaliq_list):
            tk.Label(inner, text=cd, bg=PANEL, fg=FG, font=FONT_MONO,
                     width=18, anchor="w").grid(row=i + 1, column=0, padx=4, pady=4)
            var = tk.StringVar(value="-- selecione --")
            cb = ttk.Combobox(inner, textvariable=var, values=pg_display,
                              state="readonly", width=40, font=FONT_UI)
            cb.grid(row=i + 1, column=1, padx=4, pady=4)
            var.trace_add("write", lambda *_, _cd=cd, _var=var: self._on_row_change(_cd, _var))
            self._aliq_vars[cd] = (var, self._pg_options)

        self._refresh_status()

    @property
    def mapping(self) -> dict[str, int]:
        """Returns {cdaliq_value: i_cod_bs_aliquota_c} for all mapped rows."""
        return dict(self._mapping)

    @property
    def is_complete(self) -> bool:
        return len(self._aliq_vars) > 0 and len(self._mapping) == len(self._aliq_vars)

    # ─────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────
    def _on_row_change(self, cdaliq: str, var: tk.StringVar):
        sel = var.get()
        if sel in self._pg_options:
            self._mapping[cdaliq] = self._pg_options[sel]
        else:
            self._mapping.pop(cdaliq, None)
        self._refresh_status()
        self._on_mapping_changed(self.is_complete)

    def _refresh_status(self):
        total = len(self._aliq_vars)
        done = len(self._mapping)
        if total == 0:
            self.status_label.config(text="", fg=WARNING)
        elif done == total:
            self.status_label.config(text=f"✓ {done}/{total} completo", fg=SUCCESS)
        else:
            self.status_label.config(text=f"{done}/{total} associadas", fg=WARNING)
