import logging
from pathlib import Path

def logger(log_file, to_console=False):
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('eo_logger')
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)

    # Print to terminal
    if to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    logger.addHandler(file_handler)

    return logger
    