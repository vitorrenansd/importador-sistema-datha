import threading
from tkinter import messagebox

from view.main_window import MainWindow
from model.firebird_conn import FirebirdConnection
from model.postgres_conn import PostgresConnection
from model.migrator import Migrator
from config import get_firebird_config, get_postgres_config


class AppController:
    def __init__(self, root):
        self.root = root
        self.fb = FirebirdConnection()
        self.pg = PostgresConnection()
        self.view = MainWindow(root, controller=self)

        self.view.set_fb_credentials(get_firebird_config())
        self.view.set_pg_credentials(get_postgres_config())

        self._fb_connected = False
        self._pg_connected = False

    # ─────────────────────────────────────────
    # Event handlers (called by view)
    # ─────────────────────────────────────────
    def on_test_connections(self):
        self._fb_connected = False
        self._pg_connected = False
        self.view.set_import_enabled(False)
        threading.Thread(target=self._test_connections_thread, daemon=True).start()

    def on_mapping_changed(self, is_complete: bool):
        if self._fb_connected and self._pg_connected:
            self.view.set_import_enabled(is_complete)

    def on_start_import(self):
        if not messagebox.askyesno(
            "Confirmar importação",
            "Começar importação?\nEsta ação não poderá ser desfeita"
        ):
            return
        self.view.set_import_enabled(False)
        self.view.set_progress(0)
        threading.Thread(target=self._import_thread, daemon=True).start()

    # ─────────────────────────────────────────
    # Threads
    # ─────────────────────────────────────────
    def _test_connections_thread(self):
        self._log("Testando conexões...", "info")

        fb_creds = self.view.get_fb_credentials()
        ok_fb, msg_fb = self.fb.connect(**fb_creds)
        self._log(msg_fb, "ok" if ok_fb else "err")
        self._fb_connected = ok_fb

        pg_creds = self.view.get_pg_credentials()
        ok_pg, msg_pg = self.pg.connect(**pg_creds)
        self._log(msg_pg, "ok" if ok_pg else "err")
        self._pg_connected = ok_pg

        if ok_fb and ok_pg:
            self._load_aliquotas()
        else:
            self._log("Corrija a conexão e tente novamente.", "warn")

    def _load_aliquotas(self):
        try:
            fb_list = self.fb.fetch_distinct_aliquotas()
            pg_list = self.pg.fetch_aliquotas()
            self._log(f"Firebird CDALIQ valores encontrados: {fb_list}", "info")
            self._log(f"PostgreSQL aliquotas disponíveis: {len(pg_list)}", "info")
            self.root.after(0, lambda: self.view.load_aliquotas(fb_list, pg_list))
        except Exception as e:
            self._log(f"Erro ao carregar aliquotas: {e}", "err")

    def _import_thread(self):
        self._log("=" * 60, "dim")
        self._log("INICIANDO IMPORTAÇÃO", "info")
        self._log("=" * 60, "dim")

        try:
            aliquota_map = self.view.aliquota_panel.mapping
            migrator = Migrator(self.fb, self.pg)
            result = migrator.run(
                aliquota_map=aliquota_map,
                on_progress=lambda pct: self.root.after(0, lambda p=pct: self.view.set_progress(p)),
                on_log=self._log,
            )
            self._log("=" * 60, "dim")
            self._log(f"DONE — {result}", "info")
            self._log("=" * 60, "dim")
            self.root.after(0, lambda: self.view.set_progress(100))
            self.root.after(0, lambda: messagebox.showinfo(
                "Importação completa",
                f"Finalizada.\n\n{result}"
            ))
        except Exception as e:
            self._log(f"ERRO FATAL: {e}", "err")
            try:
                self.pg.rollback()
            except Exception:
                pass
            self.root.after(0, lambda: messagebox.showerror("Erro fatal", str(e)))
        finally:
            mapping_complete = self.view.aliquota_panel.is_complete
            self.root.after(0, lambda: self.view.set_import_enabled(mapping_complete))

    # ─────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────
    def _log(self, msg: str, tag: str = ""):
        self.root.after(0, lambda m=msg, t=tag: self.view.log(m, t))
