import logging
from json import dump
from pathlib import Path

from pdfplumber import open as pdf_open
from transform.facture_tools import get_init, get_products, get_tax_details
from transform.pdf_parser import parse_date, parse_float, parse_int


class Facture:
    def __init__(self, file_path: Path):
        self.path = file_path

    def __enter__(self):
        try:
            self.pdf = pdf_open(self.path)
            logging.info(f"Facture file '{self.path}' is opened")
            return self
        except Exception as e:
            if self.path.exists():
                logging.error(f"Facture file '{self.path}' is not opened")
            else:
                logging.error(f"Facture file '{self.path}' does not exist")
            logging.error(e)
            self.pdf = None
            return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.pdf:
            self.pdf.close()
            logging.info(f"Facture file '{self.path}' is closed")
        elif self.path.exists():
            logging.error(f"Facture file '{self.path}' is not yet opened")
        else:
            logging.error(f"Facture file '{self.path}' does not exist")

    def parse(self):
        self.type = "Facture"
        d = (
            get_init(self.pdf)
            | {"produits": get_products(self.pdf)}
            | get_tax_details(self.pdf)
        )
        for key in d:
            setattr(self, key, d[key])

        self.montant_ht = parse_float(self.montant_ht)
        self.montant_ttc = parse_float(self.montant_ttc)
        self.date_facturation = parse_date(self.date_facturation)
        self.date_livraison = parse_date(self.date_livraison)
        self.echeance_facture = parse_date(self.echeance_facture)
        self.est_lub = self.est_lub is not None
        self.numero_bl = parse_int(self.numero_bl)
        self.numero_commande = parse_int(self.numero_commande)
        self.numero_facture = parse_int(self.numero_facture)
        for taux_montant in self.details_tva:
            taux_montant["montant"] = parse_float(taux_montant["montant"])
            taux_montant["taux"] = parse_float(taux_montant["taux"])

        for produit in self.produits:
            produit["code_produit"] = parse_int(produit["code_produit"])
            produit["description"] = produit["description"].replace(
                "\n", " ").strip()
            produit["quantite"] = parse_float(produit["quantite"])
            produit["prix_unitaire"] = parse_float(produit["prix_unitaire"])
            produit["taux_tva"] = parse_float(produit["taux_tva"])
            produit["montant"] = parse_float(produit["montant"])

        self.json_path = f"apps/transform/json_docs/{self.date_facturation.strftime('%y%m%d')}-f-{self.numero_facture}.json"

    def save_json(self):
        ...
        dc = {
            key: self.__dict__[key]
            for key in self.__dict__
            if key
            not in (
                "path",
                "pdf",
                "date_facturation",
                "date_livraison",
                "echeance_facture",
                "json_path",
            )
        }
        dc["date_facturation"] = self.date_facturation.strftime("%Y-%m-%d")
        dc["date_livraison"] = self.date_livraison.strftime("%Y-%m-%d")
        dc["echeance_facture"] = self.echeance_facture.strftime("%Y-%m-%d")
        with open(
            self.json_path,
            "w",
        ) as f:
            dump(obj=dc, fp=f)
