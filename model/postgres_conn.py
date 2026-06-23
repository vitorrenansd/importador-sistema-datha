try:
    import pg8000
    import pg8000.native
except ImportError:
    pg8000 = None


class PostgresConnection:
    def __init__(self):
        self.conn = None

    def connect(self, host: str, port: str, database: str, user: str, password: str) -> tuple[bool, str]:
        if pg8000 is None:
            return False, "Lib 'pg8000' não instalada. Rode no cmd: pip install pg8000"
        try:
            self.conn = pg8000.connect(
                host=host,
                port=int(port),
                database=database,
                user=user,
                password=password
            )
            self.conn.autocommit = False
            return True, f"PostgreSQL conectado: {host}:{port}/{database}"
        except Exception as e:
            self.conn = None
            return False, f"PostgreSQL erro: {e}"

    def _cursor(self):
        return self.conn.cursor()

    def fetch_aliquotas(self) -> list[dict]:
        cur = self._cursor()
        cur.execute("SELECT i_cod_bs_aliquota_c, s_descricao FROM bs_aliquota_c ORDER BY s_descricao")
        rows = cur.fetchall()
        return [{"i_cod_bs_aliquota_c": r[0], "s_descricao": r[1]} for r in rows]

    def product_exists(self, external_number: str) -> bool:
        cur = self._cursor()
        cur.execute(
            "SELECT 1 FROM m_produto_c WHERE i_numero_sistema_externo = %s",
            (external_number,)
        )
        return cur.fetchone() is not None

    def find_ncm_by_description(self, description: str) -> int | None:
        cur = self._cursor()
        cur.execute(
            "SELECT i_cod_b_ncmsh_c FROM b_ncmsh_c WHERE s_descricao = %s LIMIT 1",
            (description,)
        )
        row = cur.fetchone()
        return row[0] if row else None

    def create_ncm(self, description: str) -> int:
        cur = self._cursor()
        cur.execute("SELECT nextval('public.seq_b_ncmsh_c')")
        new_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO b_ncmsh_c (i_cod_b_ncmsh_c, s_descricao, ib_modificado) VALUES (%s, %s, 0)",
            (new_id, description)
        )
        return new_id

    def insert_product(self, data: dict) -> int:
        cur = self._cursor()
        cur.execute("SELECT nextval('public.seq_m_produto_c')")
        new_id = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO m_produto_c
               (i_cod_m_produto_c, i_numero_sistema_externo,
                s_descricao_produto, s_descricao_reduzida,
                f_preco_custo, f_preco_venda, f_estoque_atual,
                s_localizacao, i_cod_b_ncmsh_c, i_cod_bs_aliquota_c)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                new_id,
                data["external_number"],
                data["description"],
                data["description"],
                data["cost_price"],
                data["sale_price"],
                data["stock"],
                data["location"],
                data["ncm_id"],
                data["aliquota_id"],
            )
        )
        return new_id

    def insert_barcode(self, product_id: int, barcode: str):
        cur = self._cursor()
        cur.execute(
            "INSERT INTO r_produto_cod_barra_c (i_cod_m_produto_c, s_cod_barra) VALUES (%s, %s)",
            (product_id, barcode)
        )

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
