import random

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
            return False, "Lib 'pg8000' não instalada. Rodar no cmd: pip install pg8000"
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
            return False, f"PostgreSQL error: {e}"

    def _cursor(self):
        return self.conn.cursor()

    def fetch_aliquotas(self) -> list[dict]:
        cur = self._cursor()
        cur.execute("""
            SELECT
                i_cod_bs_aliquota_c,
                s_descricao
            FROM bs_aliquota_c
            ORDER BY s_descricao;
        """)
        rows = cur.fetchall()
        return [{"i_cod_bs_aliquota_c": r[0], "s_descricao": r[1]} for r in rows]

    def product_exists(self, external_number: str) -> bool:
        cur = self._cursor()
        cur.execute("""
            SELECT 1
            FROM m_produto_c
            WHERE i_numero_sistema_externo = %s;
        """,(external_number,))

        return cur.fetchone() is not None

    def find_ncm_by_description(self, description: str) -> int | None:
        cur = self._cursor()
        cur.execute("""
            SELECT
                i_cod_b_ncmsh_c
            FROM b_ncmsh_c
            WHERE s_descricao = %s
            LIMIT 1;
        """,(description,))

        row = cur.fetchone()
        return row[0] if row else None

    def create_ncm(self, description: str) -> int:
        cur = self._cursor()
        cur.execute("SELECT nextval('public.seq_b_ncmsh_c')")
        new_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO b_ncmsh_c (i_cod_b_ncmsh_c, s_descricao, ib_modificado)
            VALUES (%s, %s, 0)
        """,(new_id, description))

        return new_id
    
    def find_group_by_description(self, description: str) -> int | None:
        cur = self._cursor()
        cur.execute("""
            SELECT
                i_cod_b_grupo_produto_c
            FROM b_grupo_produto_c
            WHERE s_descricao_grupo_produto ILIKE %s
            LIMIT 1
        """,(description,))

        row = cur.fetchone()
        return row[0] if row else None
    
    def find_unit_by_abbreviation(self, abbreviation: str) -> int | None:
        cur = self._cursor()
        cur.execute("""
            SELECT i_cod_bs_unidade_produto_c
            FROM bs_unidade_produto_c
            WHERE UPPER(s_desc_red_unid_prod) = UPPER(%s)
            LIMIT 1
        """, (abbreviation,))
        row = cur.fetchone()
        return row[0] if row else None

    def create_group(self, description: str) -> int:
        cur = self._cursor()
        cur.execute("SELECT nextval('public.seq_b_grupo_produto_c')")
        new_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO b_grupo_produto_c (i_cod_b_grupo_produto_c, s_descricao_grupo_produto)
            VALUES (%s, %s)
        """,(new_id, description[:40]))
        return new_id
    
    def create_unit(self, abbreviation: str, description: str = None) -> int:
        cur = self._cursor()
        cur.execute("SELECT nextval('public.seq_bs_unidade_produto_c')")
        new_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO bs_unidade_produto_c
                (i_cod_bs_unidade_produto_c, s_descricao_unid_prod, s_desc_red_unid_prod)
            VALUES (%s, %s, %s)
        """, (new_id, description, description or abbreviation))

        return new_id

    def insert_product(self, data: dict) -> int:
        cur = self._cursor()
        cur.execute("SELECT nextval('public.seq_m_produto_c')")
        new_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO m_produto_c (
                i_cod_m_produto_c,
                s_referencia,
                i_numero_sistema_externo,
                s_descricao_produto,
                s_descricao_reduzida,
                f_preco_custo,
                f_perc_marg_lucro,
                f_preco_venda,
                f_estoque_max,
                f_estoque_min,
                f_estoque_atual,
                ib_perm_venda_frac,
                f_qtd_volume,
                f_perc_acres_frac,
                f_preco_fracao,
                s_localizacao,
                i_cod_b_ncmsh_c,
                i_cod_bs_aliquota_interna_c,
                i_cod_b_grupo_produto_c,
                i_cod_bs_unidade_produto_c,
                i_cod_b_dpto_produto_c,
                i_cod_b_sit_trib_produto_c,
                i_cod_b_tipo_estoque_c,
                i_cod_b_origem_produto_c,
                ib_promocao,
                f_peso,
                f_peso_fracao,
                ib_conceder_desconto,
                ib_produto_composto,
                ib_controla_grade,
                ib_produto_servico,
                ib_inativo
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, 0, %s, 0, 0, %s, 0, 1, 0, 0, %s, %s, %s, %s, %s, %s, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0
            )
        """,(
                new_id,
                f"{new_id}-"+str(random.randint(1, 9)),
                data["external_number"],
                data["description"],
                data["description"],
                data["cost_price"],
                data["sale_price"],
                data["stock"],
                data["location"],
                data["ncm_id"],
                data["aliquota_id"],
                data["group_id"],
                data["unit_id"],
                data["department_id"]
            ))
        return new_id

    def insert_barcode(self, product_id: int, barcode: str):
        cur = self._cursor()
        cur.execute("SELECT nextval('public.seq_r_produto_cod_barra_c')")
        new_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO r_produto_cod_barra_c (
                i_cod_r_produto_cod_barra_c,
                i_cod_m_produto_c,
                ib_fracionado,
                s_codigo_barra
            )
            VALUES (%s, %s, 0, %s)
        """,(new_id, product_id, barcode))

    def insert_stock(self, product_id: int, stock: float):
        cur = self._cursor()
        cur.execute("SELECT nextval('public.seq_d_estoque_produto_c')")
        new_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO d_estoque_produto_c (
                i_cod_m_produto_c,
                i_estoque_atual,
                i_estoque_anterior,
                dt_base_mov_estoque,
                i_cod_d_estoque_produto_c,
                i_cod_h_planta_c,
                i_estoque_liberar,
                i_estoque_liberar_anterior,
                ib_negativo,
                i_estoque_reserva,
                i_estoque_reserva_anterior,
                i_cod_h_almoxarifado_c,
                ib_pendencia
            )
            VALUES (
                %s, %s, %s, CURRENT_DATE, %s, %s,
                0, 0, 0,
                0, 0,
                NULL,
                NULL
            )
        """, (
            product_id,
            stock,
            stock,
            new_id,
            1
        ))

    def insert_prices(self, product_id: int, sale_price: float):
        cur = self._cursor()

        # PRECO PADRAO (ID 1)
        cur.execute("SELECT nextval('public.seq_r_lista_preco_produto_c')")
        id_varejo = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO r_lista_preco_produto_c (
                i_cod_r_lista_preco_produto_c,
                i_cod_m_produto_c,
                i_cod_b_tabela_preco_c,
                f_perc_margem_lucro,
                f_preco_venda,
                ib_promocao,
                f_preco_venda_promocao,
                dt_fim_promocao,
                ib_pendencia
            )
            VALUES (%s, %s, 1, 50.00, %s, 0, NULL, NULL, 0)
        """, (
            id_varejo,
            product_id,
            float(sale_price or 0)
        ))

        # PRECO ATACADO (ID 2)
        cur.execute("SELECT nextval('public.seq_r_lista_preco_produto_c')")
        id_atacado = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO r_lista_preco_produto_c (
                i_cod_r_lista_preco_produto_c,
                i_cod_m_produto_c,
                i_cod_b_tabela_preco_c,
                f_perc_margem_lucro,
                f_preco_venda,
                ib_promocao,
                f_preco_venda_promocao,
                dt_fim_promocao,
                ib_pendencia
            )
            VALUES (%s, %s, 2, 40.00, %s, 0, NULL, NULL, 0)
        """, (
            id_atacado,
            product_id,
            float(sale_price or 0)
        ))

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
