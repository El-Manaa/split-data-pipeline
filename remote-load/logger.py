import logging

def new_logger():
    log_fmt = logging.Formatter(
        fmt = "%(asctime)s - %(levelname)s - %(message)s",
        datefmt= "%Y-%m-%d %H:%M:%S"
    )
    logger = logging.Logger(__name__)
    log_handler = logging.FileHandler("apps/load.log")
    log_handler.setFormatter(log_fmt)
    logger.addHandler(hdlr = log_handler)
    return logger

