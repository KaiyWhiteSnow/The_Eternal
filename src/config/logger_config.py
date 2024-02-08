"""Logger configuration for The Eternal

Configures logging for The Eternal bot, providing both file-based and console-based output with colored formatting.

Attributes:
    log_file (str): The path to the log file ("eternal.log").
    formatter (ColoredFormatter): A formatter for colorful console output.
    file_handler (FileHandler): A file handler for logging to the specified log file.
    console_handler (StreamHandler): A console handler for logging to the standard output.

Functions:
    configure_loggers: Configures loggers to follow The Eternal's logging format.
"""

import logging
from typing import List
import sys
from colorlog import ColoredFormatter

log_file = "eternal.log"

formatter = ColoredFormatter(
    "%(asctime)s %(log_color)s%(levelname)-8s%(reset)s %(name)s || %(message)s",
    datefmt="%m/%d/%Y %I:%M:%S %p",
    reset=True,
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
    secondary_log_colors={},
    style="%",
)

file_handler = logging.FileHandler(log_file)
console_handler = logging.StreamHandler(sys.stdout)

file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
console_handler.setFormatter(formatter)


def configure_logger(loggers: List[str] = []):
    """Configures loggers to follow The Eternal's logging format.
    
    Args:
        loggers (List[str]): A list of logger names to configure.
    """
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
