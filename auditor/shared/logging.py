import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict

class AuditorFormatter(logging.Formatter):
    """Structured log formatter for the Audit Engine."""
    
    blue = "\x1b[38;5;39m"
    cyan = "\x1b[38;5;51m"
    green = "\x1b[38;5;121m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    reset = "\x1b[0m"

    format_str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    FORMATS = {
        logging.DEBUG: blue + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_auditor_logging(level=logging.INFO):
    """Initializes the Auditor Logging stack."""
    logger = logging.getLogger("auditor")
    logger.setLevel(level)

    # Console Handler with Console formatting
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(AuditorFormatter())
    logger.addHandler(ch)

    # Structured JSON File Handler for Batch audits
    fh = logging.FileHandler("auditor.log")
    fh.setFormatter(logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}'))
    logger.addHandler(fh)

    logger.info("Auditor Logging Infrastructure Initialized. System initialized.")
    return logger

# Singleton Logger for the package
auditor_logger = setup_auditor_logging()
