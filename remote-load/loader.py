from odoo.api import Environment
from odoo import SUPERUSER_ID
from odoo.modules.registry import Registry

class Loader:
    def __init__(self, env: Environment):
        self._env = env
        self._topic = None
        self.type = None

    def add(self, d: dict):
        ...

    def read(self):
        ...

    def get_tax_by_rate(self, rate: float):
        if rate not in (19.0, 13.0):
            return None
        self._env.cr.execute("""
            SELECT id from account_tax where amount = %s limit 1
        """, (rate,))
        res = self._env.cr.fetchone()
        if not res:
            return None
        return res[0]

    def get_product_by_number(self, number: int):
        ...
        self._env.cr.execute("""
            SELECT id from product_product where default_code = (%s)::text limit 1
        """, (number,))

        res = self._env.cr.fetchone()
        if res:
            return res[0]
        return None
