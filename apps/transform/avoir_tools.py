import re
from pprint import pprint

import pdfplumber
from transform.pdf_parser import parse_date, parse_float, parse_int

all_table_settings = {
    "product_table": {
        "patterns": (
            r"(?P<libelle_produit>[\w\s]+)"
            r"\s+(?P<quantite>\d*\.?\d+,?\d*)-?"
            r"\s+(?P<prix_unitaire>\d*\.?\d+,?\d*)-?"
            r"\s+(?P<montant_ht>\d*\.?\d+,?\d*)-?"
            r"\s+(?P<taux_tva>\d*\.?\d+,?\d*)-?"
            r"\s+(?P<montant_tva>\d*\.?\d+,?\d*)-?"
        ),
        "old_settings": {
            "vertical_strategy": "lines",
            "horizontal_strategy": "text",
            "min_words_vertical": 5,  # Increase for more reliable column detection
            "text_x_tolerance": 3,  # Vertical spacing between lines
            "text_y_tolerance": 1,  # Horizontal spacing between words
            "join_tolerance": 0,
            "snap_tolerance": 0,
            "intersection_tolerance": 3,  # Tolerance for cell intersections
        },
    },
    "init_settings": {
        "patterns": (
            r"Numéro de [lI]\'Avoir:?\s+(?P<numero_avoir>\d+)\n?"
            r"Date de Avoir:?\s+(?P<date_avoir>\d{2}/\d{2}/\d{4})\n?"
            r"Devise:?\s+(?P<devise>\w+)"
        )
    },
}


def get_products(pdf: pdfplumber.PDF):
    products = []
    product_table_settings = all_table_settings["product_table"]["old_settings"]
    for i, page in enumerate(pdf.pages):
        # print(f"Page {i + 1}")
        sign = page.search(r"Libellé Produit")
        top = sign[0]["bottom"] + 0.25 if sign else 0
        bottom = sorted(map(lambda x: x["bottom"], page.horizontal_edges))[1]
        crop_1 = page.crop(bbox=(0, top, page.width, bottom))
        tables = [
            z[0]
            for y in crop_1.extract_tables(product_table_settings)[0]
            if (z := [x for x in y if x != ""])
        ]
        for text in tables:
            m = re.search(
                all_table_settings["product_table"]["patterns"],
                text,
                flags=re.IGNORECASE,
            )
            if m:
                products.append(m.groupdict())
        # crop_1.to_image().debug_tablefinder(product_table_settings).show()
    return products


def get_init(pdf: pdfplumber.PDF):
    ...
    init_data = {}
    for page in pdf.pages:
        crop_1 = page.crop(bbox=(0, 90, 200, 120))
        m = re.search(
            all_table_settings["init_settings"]["patterns"], crop_1.extract_text(),
            flags=re.IGNORECASE
        )
        if m:
            init_data.update(m.groupdict())
    return init_data


def get_tax_details(pdf: pdfplumber.PDF):
    tax_patterns = {
        "details_tva": r"TVA:?\s+(?P<taux>\d+,?\d*) %\s+(?P<montant>(?:\d+\.)?\d+(?:,?\d*))",
        "montant_ttc": r"Montant TTC:?\s+(?P<montant_ttc>(?:\d+\.)?\d+(?:,?\d*))",
        "montant_ht": r"Montant hors Taxe:?\s+(?P<montant_ht>(?:\d+\.)?\d+(?:,?\d*))",
    }
    d = {"montant_ht": None, "montant_ttc": None, "details_tva": []}
    for page in pdf.pages:
        text = page.extract_text()
        for m in re.finditer(tax_patterns["details_tva"], text, flags=re.IGNORECASE):
            d["details_tva"].append(m.groupdict())
        m = re.search(tax_patterns["montant_ttc"], text, flags=re.IGNORECASE)
        if m:
            d.update(m.groupdict())
        m = re.search(tax_patterns["montant_ht"], text, flags=re.IGNORECASE)
        if m:
            d.update(m.groupdict())
    return d
