import sys
sys.path.insert(0, ".")
from odoo.api import Environment
from odoo import SUPERUSER_ID
from odoo.modules.registry import Registry
from loader import Loader
from json import load
from pprint import pprint

class LFacture(Loader):
    def __init__(self, env: Environment):
        super().__init__(env)
        self._topic = self._env['account.move']

    def add(self, d: dict):
        res = self._topic.create({
            "move_type":"in_invoice",
            "partner_id": 6,
            "currency_id": 131,
            "ref": d["numero_facture"],
            "invoice_date": d['date_facturation'],
            "line_ids": [
                (0, None, {
                    'product_id': prod_id,
                    "journal_id": 12,
                    "company_id": 1,
                    "account_id": 457,
                    'quantity': prod['quantite'],
                    'price_unit': prod['prix_unitaire'],
                    'tax_ids': [(4, self.get_tax_by_rate(prod['taux_tva']))] 
                })
                for prod in d['produits']
                if (prod_id := self.get_product_by_number(prod['code_produit']))
            ]
        })
        self._env.cr.commit()
        print(res)
        ...

    def read(self):
        self._env.cr.execute("""
            select * from carburant_purchase_order;
        """)
        res = self._env.cr.dictfetchall()
        pprint(res)

def main():
    with Registry('gp8').cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {})
        lf = LFacture(env)
        with open("250925-f-95460713.json", "r") as f:
            d = load(f)
            lf.add(d)

if __name__ == "__main__":
    main()
