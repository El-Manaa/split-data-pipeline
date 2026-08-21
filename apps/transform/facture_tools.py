import re

import pdfplumber
from transform.pdf_parser import parse_date, parse_float, parse_int

all_table_settings = {
    "init_table": {
        "pattern": (
            r"Numéro de facture:?\s+(?P<numero_facture>\d+)"
            r"(.|\n)*Date de facturation:?\s+(?P<date_facturation>\d{2}/\d{2}/\d{4})"
            r"(.|\n)*Devise:?\s+(?P<devise>\w+)"
            r"(.|\n)*Numéro BL:?\s+(?P<numero_bl>\d+)"
            r"(.|\n)*Date de livraison:?\s+(?P<date_livraison>\d{2}/\d{2}/\d{4})"
            r"(.|\n)*Numéro de commande:?\s+(?P<numero_commande>\d+)"
            r"(.|\n)*Votre référence:?\s+cde\s?(?P<est_lub>lub)?"
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
    "tax_table": {"pattern": ()},
    "product_table": {
        "patterns": (
            r"\b(?P<code_produit>\d{5,})"
            r"\s+(?P<description>(.|\n)+)"
            r"\s+(?P<quantite>\d*\.?\d+,?\d*)-?"
            r"\s+(?P<unite>\w+)-?"
            r"\s+(?P<statut_droit>[\w\(\)\s]+)-?"
            r"\s+(?P<prix_unitaire>\d*\.?\d+,?\d*)-?"
            r"(?:\s+\(%\))?"
            r"\s+(?P<taux_tva>\d*\.?\d+,?\d*)-?"
            r"\s+(?P<montant>\d*\.?\d+,?\d*)-?\b"
        ),
        "old_settings": {
            "vertical_strategy": "text",
            "horizontal_strategy": "text",
            "min_words_vertical": 5,  # Increase for more reliable column detection
            "text_x_tolerance": 3,  # Vertical spacing between lines
            "text_y_tolerance": 1,  # Horizontal spacing between words
            "join_tolerance": 0,
            "snap_tolerance": 0,
            "intersection_tolerance": 3,  # Tolerance for cell intersections
        },
        "new_settings": {},
    },
}


def get_products(pdf: pdfplumber.PDF):
    ...
    products = []
    product_table_settings = all_table_settings["product_table"]["old_settings"]
    for i, page in enumerate(pdf.pages):
        sign = page.search(r"mesure")
        if not sign:
            sign = page.search("DEPOT")
        bottom = sign[0]["bottom"] + 0.02 if sign else 0

        horizontal_lines = sorted(map(lambda x: x["top"], page.horizontal_edges))
        crop_1 = page.crop(
            bbox=(
                0,
                bottom,
                page.width,
                horizontal_lines[1],
            )
        )
        # crop_1.to_image().debug_tablefinder().show()
        tops = sorted(set(round(w["top"], 1) for w in crop_1.extract_words()))
        if tops and len(tops) > 1:
            explicit_hlines = (
                [tops[0] - 2]
                + [tops[i] for i in range(1, len(tops)) if tops[i] - tops[i - 1] > 10]
                + [tops[-1] + 10]
            )
        else:
            explicit_hlines = [0, page.height]

        lefts = sorted(set(round(w["x0"], 1) for w in crop_1.extract_words()))
        if lefts:
            explicit_vlines = (
                [lefts[0]]
                + [
                    lefts[i]
                    for i in range(1, len(lefts))
                    if lefts[i] - lefts[i - 1] > 30
                ]
                + [lefts[-1] + 35]
            )
        else:
            explicit_vlines = [0, page.width]

        all_table_settings["product_table"]["new_settings"] = (
            product_table_settings.copy()
            | {
                "horizontal_strategy": "explicit",
                "explicit_horizontal_lines": explicit_hlines,
                "vertical_strategy": "explicit",
                "explicit_vertical_lines": explicit_vlines,
            }
        )
        new_table_settings = all_table_settings["product_table"]["new_settings"]
        table = crop_1.extract_table(new_table_settings)
        # crop_1.to_image().debug_tablefinder(new_table_settings).show()
        if table:
            for tab in (" ".join(row) for row in table):
                # print(tab)
                m = re.search(all_table_settings["product_table"]["patterns"], tab, flags=re.IGNORECASE)
                if m:
                    products.append(m.groupdict())
    return products


def get_init(pdf: pdfplumber.PDF):
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "text",
        "min_words_vertical": 5,  # Increase for more reliable column detection
        "text_x_tolerance": 3,  # Vertical spacing between lines
        "text_y_tolerance": 1,  # Horizontal spacing between words
        "join_tolerance": 0,
        "snap_tolerance": 0,
        "intersection_tolerance": 3,  # Tolerance for cell intersections
    }
    first_page = pdf.pages[0]
    crop_depot = first_page.search(r"DEPOT\n")
    crop_num_com = first_page.search(r"Numéro de commande")
    d = {}
    if crop_depot and crop_num_com:
        crop_1 = first_page.crop(
            (
                0,
                crop_depot[0]["bottom"] + 2,
                first_page.width,
                crop_num_com[0]["bottom"] + 2,
            )
        )
        tops = sorted(set(round(w["top"], 1) for w in crop_1.extract_words()))
        if tops and len(tops) > 1:
            explicit_h_lines = (
                [tops[0] - 2]
                + [tops[i] for i in range(1, len(tops)) if tops[i] - tops[i - 1] > 8]
                + [tops[-1] + 10]
            )
            new_table_settings = table_settings | {
                "horizontal_strategy": "explicit",
                "explicit_horizontal_lines": explicit_h_lines,
            }
            # crop_1.to_image().debug_tablefinder(new_table_settings).show()
            tables = crop_1.extract_tables(new_table_settings)[0]
            text = " ".join(table[0] for table in tables)
            m = re.search(
                all_table_settings["init_table"]["pattern"], text, flags=re.IGNORECASE
            )
            if m:
                d.update(m.groupdict())
    me = first_page.search(r"Échéance de la facture:? (\d{2}/\d{2}/\d{4})")
    if me:
        d.update({"echeance_facture": me[0]["groups"][0]})
    return d


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
