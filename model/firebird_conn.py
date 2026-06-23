try:
    import fdb
except ImportError:
    fdb = None


class FirebirdConnection:
    def __init__(self):
        self.conn = None

    def connect(self, host: str, port: str, database: str, user: str, password: str) -> tuple[bool, str]:
        if fdb is None:
            return False, "Library 'fdb' not installed. Run: pip install fdb"
        try:
            dsn = f"{host}/{port}:{database}"
            self.conn = fdb.connect(
                dsn=dsn,
                user=user,
                password=password,
                charset="UTF8"
            )
            return True, f"Firebird conectado: {dsn}"
        except Exception as e:
            self.conn = None
            return False, f"Firebird erro: {e}"

    def fetch_distinct_aliquotas(self) -> list[str]:
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT CDALIQ FROM PRODUTOS WHERE CDALIQ IS NOT NULL ORDER BY CDALIQ")
        return [str(row[0]).strip() for row in cur.fetchall()]

    def fetch_products(self) -> list[tuple]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT CDPROD, NMPROD, CUSTOPROD, VENDAPROD,
                   ESTPROD, LOCALPRODESTOQUE, CDCLASSFISCAL,
                   CDBARRA, CDALIQ
            FROM PRODUTOS
            ORDER BY CDPROD
        """)
        return cur.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
