import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

ODOO_URL = os.getenv("ODOO_URL", "").rstrip("/")
ODOO_DB = os.getenv("ODOO_DB", "")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "")
ODOO_ENABLED = os.getenv("ODOO_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
