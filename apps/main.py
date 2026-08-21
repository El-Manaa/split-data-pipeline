from document import extract_files, transform_one_file, Path, move_to_processing
from multiprocessing import Pool
from os import listdir
from datetime import datetime


def main():
    start_date = None
    extract_files(start_date=start_date)
    # PDF_DOCS = (Path(f"apps/processing/{f}") for f in listdir("apps/processing/"))
    PDF_DOCS = move_to_processing()
    with Pool(processes=4) as pool:
        pool.map(transform_one_file, PDF_DOCS)
    

if __name__ == "__main__":
    main()
