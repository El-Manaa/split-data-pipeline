from json import dump
from pathlib import Path

from pdfplumber import open as pdf_open
from transform.avoir_tools import get_init, get_products, get_tax_details
from transform.pdf_parser import (
    parse_date,
    parse_float,
    parse_int,
)


class Avoir:
    def __init__(self, file_path: Path):
        self.path = file_path

    def __enter__(self):
        self.pdf = pdf_open(self.path)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.pdf.close()

    def parse(self):
        # assert self._identify_doc() == "Avoir", "Unknown Document"
        self.type = "Avoir"
        d = (
            get_init(self.pdf)
            | {"produits": get_products(self.pdf)}
            | get_tax_details(self.pdf)
        )

        for key in d:
            setattr(self, key, d[key])

        self.date_avoir = parse_date(self.date_avoir)
        self.montant_ht = parse_float(self.montant_ht)
        self.montant_ttc = parse_float(self.montant_ttc)
        self.numero_avoir = parse_int(self.numero_avoir)
        for prod in self.produits:
            prod["libelle_produit"] = prod["libelle_produit"].replace(
                "\n", " ").strip()
            prod["montant_ht"] = parse_float(prod["montant_ht"])
            prod["montant_tva"] = parse_float(prod["montant_tva"])
            prod["quantite"] = parse_float(prod["quantite"])
            prod["prix_unitaire"] = parse_float(prod["prix_unitaire"])
            prod["taux_tva"] = parse_float(prod["taux_tva"])

        for det in self.details_tva:
            det["taux"] = parse_float(det["taux"])
            det["montant"] = parse_float(det["montant"])

        self.json_path = f"apps/transform/json_docs/{self.date_avoir.strftime('%y%m%d')}-a-{self.numero_avoir}.json"

    def save_json(self):
        ...
        dc = {
            key: self.__dict__[key]
            for key in self.__dict__
            if key not in ("path", "pdf", "date_avoir", "json_path")
        }
        dc["date_avoir"] = self.date_avoir.strftime("%Y-%m-%d")
        with open(
            self.json_path,
            "w",
        ) as f:
            dump(obj=dc, fp=f)
