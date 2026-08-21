from l_avoir import LAvoir
from l_confirmation import LConfirmation
from l_facture import LFacture
from pathlib import Path
from odoo.api import Environment
from json import load
from logger import new_logger

def identify_document(file: Path):
    if file.suffix != ".json":
        return None
    match file.name.split("-")[1]:
        case 'f':
            return LFacture
        case 'c':
            return LConfirmation
        case 'a':
            return LAvoir
        case _:
            return None

def load_document(file: Path, env: Environment):
    if LType := identify_document(file):
        lt = LType(env)
        logger = new_logger()
        with open(file, "r") as f:
            logger.info(f"Loading document '{file}'")
            d = load(f)
            try:
                lt.add(d)
            except Exception as e:
                logger.error(f"Could not load JSON File '{file}'") 
                with open(f"apps/failed/load_err-{file.stem}.txt", "w") as ef:
                    ef.write(e)
                file.rename(f"apps/failed/{file.name}")
            else:
                logger.info(f"JSON File '{file}' is successfully loaded.")
                file.rename(f"apps/inserted/{file.name}")
