from model.firebird_conn import FirebirdConnection
from model.postgres_conn import PostgresConnection


class MigrationResult:
    def __init__(self):
        self.inserted = 0
        self.skipped = 0
        self.errors = 0

    def __str__(self):
        return f"Produtos novos: {self.inserted}  |  Pulados: {self.skipped}  |  Erros: {self.errors}"


class Migrator:
    def __init__(self, fb: FirebirdConnection, pg: PostgresConnection):
        self.fb = fb
        self.pg = pg
        self._ncm_cache: dict[str, int | None] = {}
        self._group_cache: dict[str, int] = {}
        self._unit_cache: dict[str, int] = {}

    def run(self, aliquota_map: dict[str, int], on_progress, on_log) -> MigrationResult:
        """
        aliquota_map: {cdaliq_value: i_cod_bs_aliquota_c}
        on_progress(pct: float): callback for progress bar
        on_log(msg: str, tag: str): callback for log panel
        """
        result = MigrationResult()

        # O sistema legado grava ids sem avancar as sequences, entao elas ficam
        # atras do que ja existe e o nextval devolveria um id duplicado.
        ajustadas = self.pg.sync_sequences(on_log)
        if ajustadas:
            on_log(f"{ajustadas} sequence(s) reposicionada(s) antes da importacao.", "info")
        else:
            on_log("Sequences ja estavam consistentes.", "dim")

        products = self.fb.fetch_products()
        total = len(products)
        on_log(f"Total de produtos no Firebird: {total}", "info")

        for idx, row in enumerate(products):
            (cdprod, nmprod, custo, venda,
             estoque, local, cdclassfiscal,
             cdbarra, cdaliq, nmgrupo, cdunidade) = row

            on_progress((idx + 1) / total * 100)

            cdprod_str  = str(cdprod).strip()  if cdprod  else None
            nmprod_str  = str(nmprod).strip()  if nmprod  else ""
            cdaliq_str  = str(cdaliq).strip()  if cdaliq  else None
            nmgrupo_str = str(nmgrupo).strip()  if nmgrupo else "GERAL"

            # Skip duplicates
            if self.pg.product_exists(cdprod_str):
                on_log(f"[SKIP] CDPROD={cdprod_str} já existe.", "dim")
                result.skipped += 1
                continue

            # Resolve aliquota
            aliquota_id = aliquota_map.get(cdaliq_str)
            if not aliquota_id:
                on_log(f"[ERROR] CDPROD={cdprod_str} CDALIQ '{cdaliq_str}' não associada. Pulando.", "err")
                result.errors += 1
                continue

            ncm_id = self._resolve_ncm(cdclassfiscal, on_log)
            group_id = self._resolve_group(nmgrupo_str, on_log)
            unit_id = self._resolve_unit(cdunidade, None, on_log)

            # Insert product + barcode
            try:
                product_data = {
                    "external_number": cdprod_str,
                    "description":     nmprod_str,
                    "cost_price":      float(custo)   if custo   is not None else 0.0,
                    "sale_price":      float(venda)   if venda   is not None else 0.0,
                    "stock":           float(estoque) if estoque is not None else 0.0,
                    "location":        str(local).strip() if local else None,
                    "ncm_id":          ncm_id,
                    "aliquota_id":     aliquota_id,
                    "group_id":        group_id,
                    "unit_id":         unit_id,
                    "department_id": 1,
                }
                new_id = self.pg.insert_product(product_data)
                self.pg.insert_barcode(new_id, str(cdbarra).strip())
                self.pg.insert_stock(new_id, float(estoque or 0))
                self.pg.insert_prices(new_id, float(venda or 0))

                self.pg.commit()
                on_log(f"[OK] CDPROD={cdprod_str} '{nmprod_str[:40]}'. id={new_id}", "ok")
                result.inserted += 1

            except Exception as e:
                self.pg.rollback()
                on_log(f"[ERROR] CDPROD={cdprod_str}: {e}", "err")
                result.errors += 1

        return result

    def _resolve_ncm(self, cdclassfiscal, on_log) -> int | None:
        if not cdclassfiscal:
            return None

        cf_str = str(cdclassfiscal).strip()

        if cf_str in self._ncm_cache:
            return self._ncm_cache[cf_str]

        ncm_id = self.pg.find_ncm_by_description(cf_str)
        if ncm_id:
            on_log(f"  NCM encontrado: '{cf_str}'. id={ncm_id}", "dim")
        else:
            ncm_id = self.pg.create_ncm(cf_str)
            on_log(f"  NCM criado: '{cf_str}'. id={ncm_id}", "warn")

        self._ncm_cache[cf_str] = ncm_id
        return ncm_id
    
    def _resolve_group(self, nmgrupo: str, on_log) -> int:
        if nmgrupo in self._group_cache:
            return self._group_cache[nmgrupo]
 
        group_id = self.pg.find_group_by_description(nmgrupo)
        if group_id:
            on_log(f"  Grupo encontrado: '{nmgrupo}'. id={group_id}", "dim")
        else:
            group_id = self.pg.create_group(nmgrupo)
            on_log(f"  Grupo criado: '{nmgrupo}'. id={group_id}", "warn")
 
        self._group_cache[nmgrupo] = group_id
        return group_id
    
    def _resolve_unit(self, fb_unit_code: str | None, fb_unit_name: str | None, on_log) -> int:
        key = str(fb_unit_name or fb_unit_code or "UN").strip()

        if key in self._unit_cache:
            return self._unit_cache[key]

        unit_id = self.pg.find_unit_by_abbreviation(key)

        if unit_id:
            on_log(f"  Unidade encontrada: '{key}'. id={unit_id}", "dim")
        else:
            unit_id = self.pg.create_unit(key, fb_unit_name)
            on_log(f"  Unidade criada: '{key}'. id={unit_id}", "warn")

        self._unit_cache[key] = unit_id
        return unit_id
