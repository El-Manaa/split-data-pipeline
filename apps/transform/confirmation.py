from json import dump
from pathlib import Path

from pdfplumber import open as pdf_open
from transform.confirmation_tools import (
    get_init,
    get_products,
    get_tax_details,
)
from transform.pdf_parser import (
    parse_date,
    parse_float,
    parse_int,
)


class Confirmation:
    def __init__(self, file_path: Path):
        self.path = file_path

    def __enter__(self):
        self.pdf = pdf_open(self.path)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.pdf.close()

    def parse(self):
        self.type = "Confirmation de Commande"
        d = (
            get_init(self.pdf)
            | {"produits": get_products(self.pdf)}
            | get_tax_details(self.pdf)
        )
        for key in d:
            setattr(self, key, d[key])

        self.montant_ht = parse_float(self.montant_ht)
        self.montant_ttc = parse_float(self.montant_ttc)
        self.date_commande = parse_date(self.date_commande)
        self.numero_commande = parse_int(self.numero_commande)
        self.est_lub = self.est_lub is not None
        self.date_livraison = parse_date(self.date_livraison)
        for details in self.details_tva:
            details["taux"] = parse_float(details["taux"])
            details["montant"] = parse_float(details["montant"])
        for produit in self.produits:
            produit["code_produit"] = parse_int(produit["code_produit"])
            produit["description"] = produit["description"].replace(
                "\n", " ").strip()
            produit["quantite"] = parse_float(produit["quantite"])
            produit["prix_unitaire"] = parse_float(produit["prix_unitaire"])
            produit["taux_tva"] = parse_float(produit["taux_tva"])
            produit["montant"] = parse_float(produit["montant"])

        self.json_path = f"apps/transform/json_docs/{self.date_commande.strftime('%y%m%d')}-c-{self.numero_commande}.json"


    def save_json(self):
        ...
        dc = {
            key: self.__dict__[key]
            for key in self.__dict__
            if key not in ("path", "pdf", "date_commande", "date_livraison", "json_path")
        }
        dc["date_commande"] = self.date_commande.strftime("%Y-%m-%d")
        dc["date_livraison"] = self.date_livraison.strftime("%Y-%m-%d")
        with open(
            self.json_path,
            "w",
        ) as f:
            dump(obj=dc, fp=f)
