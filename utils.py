class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_warn(message):
    """Print a warning message to the console."""
    print(f"{bcolors.WARNING}{message}{bcolors.ENDC}")

def print_error(message):
    """Print an error message to the console."""
    print(f"{bcolors.FAIL}{message}{bcolors.ENDC}")