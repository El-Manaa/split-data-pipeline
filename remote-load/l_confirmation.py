from odoo.api import Environment
from pprint import pprint
from loader import Loader

class LConfirmation(Loader):
    def __init__(self, env: Environment):
        super().__init__(env)
        self._topic = self._env['purchase.order']

    def add(self, d: dict):
        res = self._topic.create({
            "partner_id": 6,
            "currency_id": 131,
            "date_order": d['date_commande'],
            "date_planned": d['date_livraison'],
            "order_line": [
                (0, None, {
                    'product_id': prod_id,
                    'product_qty': prod['quantite'],
                    'price_unit': prod['prix_unitaire'],
                    'tax_ids': [(4, self.get_tax_by_rate(prod['taux_tva']))] 
                })
                for prod in d['produits']
                if (prod_id := self.get_product_by_number(prod['code_produit']))
            ]
        })
        print(res)
        
        
    def read(self):
        self.__env.cr.execute(r"""
            select *
            from account_tax --product_template
            --where order_id = 25
            limit 1
            --where display_name ~ '\[61993\].+'
        """)
        recs = self.__env.cr.dictfetchall()
        pprint(recs)
        ...

