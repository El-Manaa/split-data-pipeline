import sys
sys.path.insert(0, ".")
from odoo.api import Environment
from loader import Loader
from odoo import SUPERUSER_ID
from odoo.modules.registry import Registry
from json import load
from pprint import pprint

class LAvoir(Loader):
    ...
    def __init__(self, env: Environment):
        self._env = env
        self._topic = self._env['account.move']
        
    def get_product_by_name(self, name):
        self._env.cr.execute("""
            select id from product_template where lower(name->>'fr_FR') = lower(%s);
        """, (name,))
        res = self._env.cr.fetchone()
        if not res:
            return None
        return res[0]
        

    def add(self, d: dict):
        self._topic.create({
            "move_type":"in_refund",
            "partner_id": 6,
            "currency_id": 131,
            "ref": d["numero_avoir"],
            "invoice_date": d['date_avoir'],
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
                if (prod_id := self.get_product_by_name(prod['libelle_produit']))
            ]
        })

    def read(self):
        self._topic.cr.execute("""
            select * from account_move where move_type = 'in_refund'
        """)
        res = self._topic.cr.dictfetchall()
        if res:
            print(res)

def main():
    ...
    with Registry('gp8').cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            la = LAvoir(env)
            with open("260514-a-33282398.json", "r") as f:
                d = load(f)
                la.add(d)

if __name__ == "__main__":
    main()
