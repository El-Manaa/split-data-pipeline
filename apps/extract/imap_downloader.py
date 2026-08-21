import email
import imaplib
from datetime import datetime, timedelta
from io import BytesIO
from os import listdir
from pathlib import Path
from logger import new_logger
from dotenv import dotenv_values
from pdfplumber import open as pdf_open

IMAP_CONFIG = dotenv_values("apps/extract/.env") | {"USE_SSL": True}
logger = new_logger(False)

def identify_doc(pdf_file: Path | BytesIO):
    with pdf_open(pdf_file) as pdf:
        # print(pdf)
        title = pdf.pages[0].crop(bbox=(227, 0, 480, 70)).extract_text().lower()
        print(title)
        match title:
            case "facture":
                return "f"
            case "confirmation de la commande":
                return "c"
            case "avoir":
                return "a"
            case _:
                return ""


class IMAP_Downloader:
    def __init__(self, config=IMAP_CONFIG):
        self.mail = None
        self.config = config
        self.store_path = "apps/incoming/"

    def __enter__(self):
        self.mail = imaplib.IMAP4_SSL(
            self.config["SERVER"],
            self.config["PORT"],
        )
        try:
            ok = self.mail.login(self.config["GP8_EMAIL"], self.config["GP8_PASSWORD"])[0]
            if ok != 'OK':
                raise Exception("No OK")
            else:
                logger.info("Successfully connected to Gmail Service")
                return self
        except Exception as e:
            logger.error("Cannot connect to Gmail Service")
            print(e)
            return None

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if self.mail:
            self.mail.logout()
            logger.info("Disconnected from Gmail Service")


    def get_last_datetime(self) -> datetime:
        ...
        ls = listdir(self.store_path)
        if ls:
            s = max(
                x.split("-")[0]
                for x in ls
            )
            return datetime.strptime(s, "%y%m%d") + timedelta(days=1)
        else:
            d = datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            
            return d

    def extract(
        self, start_date: datetime = datetime.now().replace(day=1)
    ):
        if self.mail:
            logger.info("Starting mail extraction")
            self.mail.select("inbox")
            criteria = f'FROM "@vivoenergy.com" SINCE {start_date.strftime("%d-%b-%Y")}'
            status, messages = self.mail.search(None, criteria)
            if status == "OK" and messages:
                for email_msg in (
                    email_message
                    for email_id in messages[0].split()
                    if (status_msg_data := self.mail.fetch(email_id, "(BODY.PEEK[])"))
                    and status_msg_data[0] == "OK"
                    and (
                        email_message := email.message_from_bytes(
                            status_msg_data[1][0][1]
                        )
                    )
                    and (
                        "@vivoenergy.com"
                        in email_message.get("From", "unknown").lower()
                    )
                ):
                    date_str = email_msg.get("Date")
                    email_date = (
                        email.utils.parsedate_to_datetime(date_str)
                        if date_str
                        else datetime.now()
                    ).replace(tzinfo=None)
                    self.lst = []
                    for att in (
                        {"part": part, "data": payload, "filename": original_filename}
                        for part in email_msg.walk()
                        if part.get_content_maintype() != "multipart"
                        and part.get("Content-Disposition") is not None
                        and (
                            part.get_content_type() == "application/pdf"
                            or (filename := part.get_filename())
                            and filename.lower().endswith(".pdf")
                        )
                        and (payload := part.get_payload(decode=True))
                        and (original_filename := part.get_filename())
                    ):
                        if bs := BytesIO(att["data"]):
                            i = identify_doc(bs)
                            filename_stem = (
                                f"{email_date.strftime('%y%m%d-%H%M%S')}-{i}"
                            )
                            if not i:
                                with open(f"apps/failed/{filename_stem}.pdf", "wb") as f:
                                    f.write(bs.getvalue())
                            else:
                                j = sum(
                                    1
                                    for fname in self.lst
                                    if fname.split("_")[0] == filename_stem
                                )

                                if j:
                                    new_filename = filename_stem + f"_{j}"
                                elif filename_stem not in self.lst:
                                    new_filename = filename_stem

                                with open(
                                    f"apps/incoming/{new_filename}.pdf",
                                    "wb",
                                ) as f:
                                    try:
                                        f.write(bs.getvalue())
                                        logger.info(
                                            f"Document '{
                                                new_filename
                                            }.pdf' has been created"
                                        )
                                    except Exception:
                                        logger.info(
                                            f"Could not create the document '{
                                                new_filename
                                            }.pdf'"
                                        )
            logger.info("End of mail extraction")
        else:
            logger.error("No mail instance")
