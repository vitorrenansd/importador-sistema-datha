from config import get_firebird_config
import fdb

class FirebirdConnection:
    def __init__(self):
        self.conn = None

    def connect(self, host, port, database, user, password):
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
            return False, f"Firebird erro: {e}"

    def fetch_distinct_aliquotas(self) -> list[str]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT DISTINCT CDALIQ
            FROM PRODUTOS
            WHERE CDALIQ IS NOT NULL
            ORDER BY CDALIQ
        """)
        return [str(row[0]).strip() for row in cur.fetchall()]

    def fetch_products(self) -> list[tuple]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT
                p.CDPROD,
                p.NMPROD,
                p.CUSTOPROD,
                p.VENDAPROD,
                p.ESTPROD,
                p.LOCALPRODESTOQUE,
                p.CDCLASSFISCAL,
                p.CDBARRA,
                p.CDALIQ,
                g.NMGRUPO,
                p.CDUNIDADE
            FROM PRODUTOS p
            LEFT JOIN GRUPOS g ON g.CDGRUPO = p.CDGRUPO
            ORDER BY CDPROD
        """)
        return cur.fetchall()

    def fetch_groups(self) -> list[str]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT
                NMGRUPO
            FROM GRUPOS
            WHERE NMGRUPO IS NOT NULL
            ORDER BY NMGRUPO
        """)
        return [str(row[0]).strip() for row in cur.fetchall()]
    
    def fetch_units(self) -> list[tuple]:
        cur = self.conn.cursor()
        cur.execute("""
            SELECT
                CDUNIDADE,
                NMUNIDADE,
                DESCRICAO
            FROM UNIDADES
        """)
        return cur.fetchall()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
