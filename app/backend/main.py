import os

from dotenv import load_dotenv

from app import create_app
from load_azd_env import load_azd_env
from settings import Settings, load_key_vault_secrets

# Determine app mode early to load configuration sources
app_mode = os.getenv("APP_MODE", "local").lower()

# WEBSITE_HOSTNAME is always set by App Service, RUNNING_IN_PRODUCTION is set in main.bicep
RUNNING_ON_AZURE = os.getenv("WEBSITE_HOSTNAME") is not None or os.getenv("RUNNING_IN_PRODUCTION") is not None

if app_mode == "local":
    load_dotenv()
    if not RUNNING_ON_AZURE:
        load_azd_env()
elif app_mode in ("staging", "production"):
    load_key_vault_secrets()

settings = Settings()

app = create_app()
