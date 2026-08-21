import sys
sys.path.insert(0, "apps")
from l_document import load_document
from os import listdir
from pathlib import Path
from odoo import SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo.api import Environment


def main():
    ...
    if RECEIVED := listdir("apps/received/"):
        with Registry("gp8").cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, {})
            for file in RECEIVED:
                pf = Path(f"apps/received/{file}")
                load_document(pf, env)

if __name__ == "__main__":
    main()

