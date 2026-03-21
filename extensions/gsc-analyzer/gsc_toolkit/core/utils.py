"""Utility functions for GSC Toolkit."""


class Colors:
    """Terminal colors for pretty output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    YELLOW = '\033[93m'  # Alias for WARNING
    FAIL = '\033[91m'
    RED = '\033[91m'  # Alias for FAIL
    ENDC = '\033[0m'
    RESET = '\033[0m'  # Alias for ENDC
    BOLD = '\033[1m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'


def print_header(text: str):
    """Print a header with visual styling."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print a success message."""
    print(f"{Colors.GREEN}  {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print a warning message."""
    print(f"{Colors.WARNING}  {text}{Colors.ENDC}")


def print_error(text: str):
    """Print an error message."""
    print(f"{Colors.FAIL}  {text}{Colors.ENDC}")


def print_info(text: str):
    """Print an info message."""
    print(f"{Colors.CYAN}  {text}{Colors.ENDC}")
