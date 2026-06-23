from model.firebird_conn import FirebirdConnection
from model.postgres_conn import PostgresConnection


class MigrationResult:
    def __init__(self):
        self.inserted = 0
        self.skipped = 0
        self.errors = 0

    def __str__(self):
        return f"Inserted: {self.inserted}  |  Skipped: {self.skipped}  |  Errors: {self.errors}"


class Migrator:
    def __init__(self, fb: FirebirdConnection, pg: PostgresConnection):
        self.fb = fb
        self.pg = pg
        self._ncm_cache: dict[str, int | None] = {}

    def run(self, aliquota_map: dict[str, int], on_progress, on_log) -> MigrationResult:
        """
        aliquota_map: {cdaliq_value: i_cod_bs_aliquota_c}
        on_progress(pct: float): callback for progress bar
        on_log(msg: str, tag: str): callback for log panel
        """
        result = MigrationResult()
        products = self.fb.fetch_products()
        total = len(products)
        on_log(f"Total products in Firebird: {total}", "info")

        for idx, row in enumerate(products):
            (cdprod, nmprod, custo, venda,
             estoque, local, cdclassfiscal,
             cdbarra, cdaliq) = row

            on_progress((idx + 1) / total * 100)

            cdprod_str  = str(cdprod).strip()  if cdprod  else None
            nmprod_str  = str(nmprod).strip()  if nmprod  else ""
            cdaliq_str  = str(cdaliq).strip()  if cdaliq  else None

            # Skip duplicates
            if self.pg.product_exists(cdprod_str):
                on_log(f"[SKIP] CDPROD={cdprod_str} already exists.", "dim")
                result.skipped += 1
                continue

            # Resolve aliquota
            aliquota_id = aliquota_map.get(cdaliq_str)
            if not aliquota_id:
                on_log(f"[ERROR] CDPROD={cdprod_str} → CDALIQ '{cdaliq_str}' not mapped. Skipping.", "err")
                result.errors += 1
                continue

            # Resolve NCM
            ncm_id = self._resolve_ncm(cdclassfiscal, on_log)

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
                }
                new_id = self.pg.insert_product(product_data)

                if cdbarra:
                    self.pg.insert_barcode(new_id, str(cdbarra).strip())

                self.pg.commit()
                on_log(f"[OK] CDPROD={cdprod_str} '{nmprod_str[:40]}' → id={new_id}", "ok")
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
            on_log(f"  NCM found for '{cf_str}' → #{ncm_id}", "dim")
        else:
            ncm_id = self.pg.create_ncm(cf_str)
            on_log(f"  NCM created: '{cf_str}' → #{ncm_id}", "warn")

        self._ncm_cache[cf_str] = ncm_id
        return ncm_id
