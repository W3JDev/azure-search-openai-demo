import os

from app import create_app
from load_azd_env import load_azd_env
from settings import Settings, load_env_if_local

# WEBSITE_HOSTNAME is always set by App Service, RUNNING_IN_PRODUCTION is set in main.bicep
RUNNING_ON_AZURE = os.getenv("WEBSITE_HOSTNAME") is not None or os.getenv("RUNNING_IN_PRODUCTION") is not None

if not RUNNING_ON_AZURE:
    load_azd_env()

# Load environment variables and instantiate settings based on app mode
settings: Settings = load_env_if_local()

app = create_app()
