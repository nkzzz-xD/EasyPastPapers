import os
import platform
from constants import YELLOW, RED, RESET

def open_file(path: str) -> None:
    """
    Opens a file using the default application for the file type on the user's OS.

    Args:
        path (str): The path to the file to open.

    Returns:
        None
    """
    print(f"🧾 Opening file at {path}...")
    try:
        if platform.system() == "Windows":
            os.startfile(os.path.abspath(path))
        elif platform.system() == "Darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')
    except Exception as e:
        print_error(f"Could not open the file: {YELLOW}'{path}'{RESET}", f"Try opening it manually with a PDF viewer.\n{e}")

def print_error(
    erorr_message: str,
    description: str = None,
    usage: str = None,
    disable_help: bool = False
) -> None:
    """
    Prints a formatted error message to the console.

    Args:
        erorr_message (str): The main error message.
        description (str, optional): Additional description for the error.
        usage (str, optional): Usage string to display.
        disable_help (bool, optional): If True, does not print the help suggestion.

    Returns:
        None
    """
    description = f":{RESET}{description}" if description else f"{RESET}"
    print(f"\r❌ {RED}{erorr_message}{description}")
    if usage:
        print(f"{usage}")
    if not disable_help:
        print("Type 'help' to see available commands.")

def program_exit() -> None:
    """
    Exits the program gracefully, printing a message.

    Returns:
        None
    """
    print(f"{YELLOW}Exiting program...{RESET}", end="")
    raise SystemExit(0)