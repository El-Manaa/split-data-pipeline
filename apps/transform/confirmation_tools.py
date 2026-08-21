import re
from pprint import pprint

import pdfplumber
from transform.pdf_parser import parse_date, parse_float, parse_int

confirmation_path = "../../../../new/pdf-vivo-2026/2025-10-02_cacc_431020302.pdf"
abnormal_confirmation_path = (
    "../../../../new/pdf-vivo-2026/2025-11-26_lub_cac_432969494.pdf"
)

all_table_settings = {
    "init_table": {
        "pattern": (
            r"Numéro de Commande:?\s+(?P<numero_commande>\d+)"
            r"(.|\n)*Date de la commande:?\s+(?P<date_commande>\d{2}/\d{2}/\d{4})"
            r"(.|\n)*Votre numéro de référence:?\s+cde\s?(?P<est_lub>lub)?"
            r"(.|\n)*Date de livraison:?\s+(?P<date_livraison>\d{2}/\d{2}/\d{4})"
            r"(.|\n)*Devise:?\s+(?P<devise>\w+)"
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
    products = []
    product_table_settings = all_table_settings["product_table"]["old_settings"]
    for i, page in enumerate(pdf.pages):
        horizontal_lines = sorted(map(lambda x: x["top"], page.horizontal_edges))
        sign = page.search("mesure")
        if sign:
            crop_1 = page.crop(
                bbox=(0, sign[0]["bottom"] + 0.25, page.width, horizontal_lines[3])
            )
        else:
            crop_1 = page.crop(
                bbox=(0, horizontal_lines[1], page.width, horizontal_lines[2])
            )
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
    ...
    page = pdf.pages[0]
    top = page.search("Numéro de Commande")
    bottom = page.search("Devise")
    d = {}
    if top and bottom:
        crop_1 = page.crop(
            bbox=(top[0]["x0"], top[0]["top"], page.width, bottom[0]["bottom"])
        )
        m = re.search(
            all_table_settings["init_table"]["pattern"],
            crop_1.extract_text(),
            flags=re.IGNORECASE,
        )
        if m:
            d.update(m.groupdict())
    return d


def get_tax_details(pdf: pdfplumber.PDF):
    ...
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
