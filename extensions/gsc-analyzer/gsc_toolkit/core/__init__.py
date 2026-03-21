"""Core module - configuration, models, and utilities."""

from .config import (
    KEY_FILE,
    SITE_URL,
    BASE_URL,
    DEFAULT_DAYS,
    PAGESPEED_API_KEY,
    OUTPUT_DIR,
    SCOPES_READONLY,
    SCOPES_WRITE,
)
from .models import Priority, ManualAction, SEOAuditResult
from .utils import (
    Colors,
    print_header,
    print_success,
    print_warning,
    print_error,
    print_info,
)

__all__ = [
    "KEY_FILE",
    "SITE_URL",
    "BASE_URL",
    "DEFAULT_DAYS",
    "PAGESPEED_API_KEY",
    "OUTPUT_DIR",
    "SCOPES_READONLY",
    "SCOPES_WRITE",
    "Priority",
    "ManualAction",
    "SEOAuditResult",
    "Colors",
    "print_header",
    "print_success",
    "print_warning",
    "print_error",
    "print_info",
]
