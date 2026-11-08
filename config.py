# config.py
import logging
import os
from dotenv import load_dotenv

# Load the .env file first
load_dotenv()

# Toggle level based on .env
is_debug = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
log_level = logging.DEBUG if is_debug else logging.INFO

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler("finance_app.log"),
        logging.StreamHandler()
    ]
)

# Extract variables
#These specific names like mysql_db or root etc are just in case env file fails.
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql_db'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'personal_finance'),
    'port': int(os.getenv('DB_PORT', 3306))
}

AI_MODEL = os.getenv('OLLAMA_MODEL', 'llama3')

# Instantiate module-level logger
logger = logging.getLogger(__name__)

logger.info("Configuration and Logging initialized successfully.")