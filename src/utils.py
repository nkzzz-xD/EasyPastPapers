import os
import platform
from constants import YELLOW, RED, RESET

def open_file(path):
    print("🧾 Opening after download...")
    try:
        if platform.system() == "Windows":
            os.startfile(os.path.abspath(path))
        elif platform.system() == "Darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')
    except Exception as e:
        print_error(f"Could not open the file: {YELLOW}'{path}'{RESET}", f"Try opening it manually with a PDF viewer.\n{e}")

def print_error(erorr_message, description=None, usage = None, disable_help=False):
    description = f":{RESET}{description}" if description else f"{RESET}"
    print(f"\r❌ {RED}{erorr_message}{description}")
    if usage:
        print(f"{usage}")
    if not disable_help:
        print("Type 'help' to see available commands.")

def program_exit():
    print(f"{YELLOW}Exiting program...{RESET}", end="")
    raise SystemExit(0)