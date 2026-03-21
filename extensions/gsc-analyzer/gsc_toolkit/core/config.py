"""Configuration and constants for GSC Toolkit."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from CWD
load_dotenv(dotenv_path=Path.cwd() / '.env')

# Service Account Configuration
KEY_FILE = os.getenv('GSC_KEY_FILE', './service-account-key.json')
SITE_URL = os.getenv('GSC_SITE_URL', '')
BASE_URL = os.getenv('SEO_BASE_URL', '')  # e.g., https://your-domain.com

# API Configuration
DEFAULT_DAYS = int(os.getenv('GSC_DEFAULT_DAYS', '28'))
PAGESPEED_API_KEY = os.getenv('PAGESPEED_API_KEY', '')  # Optional, increases quota

# API Scopes
SCOPES_READONLY = ['https://www.googleapis.com/auth/webmasters.readonly']
SCOPES_WRITE = [
    'https://www.googleapis.com/auth/webmasters',
    'https://www.googleapis.com/auth/indexing',
]

# Output directory
OUTPUT_DIR = Path(os.getenv('GSC_OUTPUT_DIR', './output'))
OUTPUT_DIR.mkdir(exist_ok=True)
