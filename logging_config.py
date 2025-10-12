import logging
import sys
import os
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
os.makedirs("./logs", exist_ok=True)

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# ===== Main logger (general + database logs) =====
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),  # Console
        RotatingFileHandler(
            "./logs/app.log",
            maxBytes=5_000_000,
            backupCount=3,
            encoding="utf-8"
        ),
    ],
)

# ===== Separate error logger (500 errors only) =====
error_handler = RotatingFileHandler(
    "./logs/errors.log",
    maxBytes=5_000_000,
    backupCount=3,
    encoding="utf-8"
)
error_handler.setLevel(logging.ERROR)

error_logger = logging.getLogger("errors")
error_logger.addHandler(error_handler)
error_logger.setLevel(logging.ERROR)
error_logger.propagate = False

# ===== Reduce noise from dependencies =====
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

# ===== Your app logger =====
logger = logging.getLogger("app")
