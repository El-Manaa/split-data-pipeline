from os import listdir
from pathlib import Path
from traceback import format_exc
from logger import new_logger
from extract.imap_downloader import IMAP_Downloader
from transform.avoir import Avoir
from transform.confirmation import Confirmation
from transform.facture import Facture
from datetime import datetime


def extract_files(start_date: datetime = None):
    with IMAP_Downloader() as ido:
        since_date = start_date or ido.get_last_datetime()
        ido.extract(start_date=since_date)

def move_to_processing():
    return (Path(f"apps/incoming/{f}").move_into("apps/processing/") for f in listdir("apps/incoming/"))

def transform_one_file(file: Path):
    logger = new_logger(True)
    if "a" in file.stem:
        Type = Avoir
    elif "c" in file.stem:
        Type = Confirmation
    elif "f" in file.stem:
        Type = Facture
    else:
        Type = None
    if Type:
        with Type(file) as doc:
            try:
                doc.parse()
            except Exception as e:
                sp = Path(f"apps/failed/{file.name}")
                if not sp.exists(follow_symlinks=False):
                    file.move(sp)
                failed_path = Path("apps/failed/err-" + sp.stem + ".txt")
                with open(
                    failed_path,
                    "w",
                ) as f:
                    f.write(format_exc())
                logger.error(f"Could not parse document '{file.name}', review {sp} and {failed_path}")
            else:
                logger.info(f"Document '{file.name}' parsed successfully in JSON format to file '{doc.json_path}'")
                try:
                    doc.save_json()
                except Exception as e:
                    logger.error(f"Could not save JSON file '{doc.json_path}'")
                else:
                    file.move(Path(f"apps/processing/{file.name}"))
                    logger.info(f"JSON file '{doc.json_path}' saved successfully")



def main():
    ...

if __name__ == "__main__":
    main()
