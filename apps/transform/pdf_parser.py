import os
from datetime import date
from json import load
from pprint import pprint
from re import compile, finditer

import pdfplumber
import polars as pl
from pdfplumber.page import Page

...
PATHS = {
    "avoir": "./apps/docs/2025-09-16_av_32661539.pdf",
    "facture": "./apps/docs/2025-09-16_facc_95424551.pdf",
    "confirmation": "./apps/docs/2025-09-16_cacc_430452011.pdf",
}
facc_path = "../new/pdf-vivo-2026/2025-09-30_facc_95477878.pdf"


def parse_dict_by_patterns(d: dict) -> dict:
    for key in d:
        if not isinstance(d[key], list):
            yield {key: parse_by_pattern(d[key])}
        else:
            for item in d[key]:
                yield parse_dict_by_patterns(item)


def parse_by_pattern(string: str) -> int | str | date | float | None:
    ...
    try:
        if compile(r"\d+").match(string):
            return int(string)
        elif compile(r"\d*\.?\d+,?\d*").match(string):
            return float(string)
        elif compile(r"\d{2}/\d{2}/\d{4}").match(string):
            return date.strptime(string, "%d/%m/%Y")
        else:
            return string
    except Exception:
        return None


def parse_int(string: str) -> int | None:
    ...
    try:
        return int(string)
    except Exception:
        return None


def parse_date(string: str) -> date | None:
    ...
    try:
        return date.strptime(string, "%d/%m/%Y")
    except Exception:
        return None


def parse_float(string: str) -> float | None:
    ...
    try:
        return float(string.replace(".", "").replace(",", "."))
    except Exception:
        return None


def main4():
    pattern = (
        r"\b(?P<code_produit>\d{5,})"
        r"\s+(?P<description>[\w\s-]+)"
        r"\s+(?P<quantite>\d*\.?\d+,?\d*)-?"
        r"\s+(?P<unite>\w+)-?"
        r"\s+(?P<statut_droit>[\w\(\)\s]+)-?"
        r"\s+(?P<prix_unit>\d*\.?\d+,?\d*)-?"
        r"\s+(?P<taux_tva>\d*\.?\d+,?\d*)-?"
        r"\s+(?P<montant>\d*\.?\d+,?\d*)-?\b"
    )
    with pdfplumber.open(PATHS["facture"]) as pdf:
        crops = []
        for page in pdf.pages:
            crops.append(separate_page(page))
        print(crops)


def get_bbox(page: Page, lit: str, regex: bool = True) -> tuple:
    d = page.search(lit, regex=regex)[0]
    return (d["x0"], d["top"], d["x1"], d["bottom"])


def separate_page(page: Page) -> list[tuple[int, int]]:
    return sorted(
        set([(line["top"], line["bottom"]) for line in page.horizontal_edges]),
        key=lambda x: x[0],
    )


def get_sections(page: Page):
    sections = []
    horizontal_lines = sorted(page.horizontal_edges, key=lambda x: x["top"])
    y_positions = (
        [0]
        + [x["top"] for x in horizontal_lines if x["top"] < x["bottom"]]
        + [page.height]
    )

    for i in range(len(y_positions) - 1):
        top = y_positions[i]
        bottom = y_positions[i + 1]
        section = page.crop(bbox=(0, top, page.width, bottom))
        sections.append(section)

    return sections


if __name__ == "__main__":
    main4()
