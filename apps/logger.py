import logging

def new_logger(e_or_t: bool = False):
    log_fmt = logging.Formatter(
        fmt = "%(asctime)s - %(levelname)s - %(message)s",
        datefmt= "%Y-%m-%d %H:%M:%S"
    )
    logger = logging.Logger(__name__)
    log_handler = logging.FileHandler(
        f"apps/{'extract/extraction' if not e_or_t else 'transform/transformation'}.log")
    log_handler.setFormatter(log_fmt)
    logger.addHandler(hdlr = log_handler)
    return logger

def text_logger():
    log_fmt = logging.Formatter(
        fmt = "%(asctime)s - %(levelname)s - %(message)s",
        datefmt= "%Y-%m-%d %H:%M:%S"
    )
    logger = logging.Logger(__name__)
    log_handler = logging.FileHandler("apps/texts_log.log")
    log_handler.setFormatter(log_fmt)
    logger.addHandler(hdlr = log_handler)
    return logger
