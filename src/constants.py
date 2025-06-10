import re
from pathlib import Path
import os
import platform
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[36m"
GREEN = "\033[92m"
RESET = "\033[0m"
BASE_URL = "https://papers.gceguide.cc"

def get_default_download_folder() -> str:
    """
    Returns the default download folder path for past papers.
    Attempts to use the user's Downloads folder; falls back to a relative path if not possible.

    Returns:
        str: The path to the default download folder.
    """
    try:
        # Attempt to use the user's Downloads folder
        downloads_path = Path.home() / "Downloads" / "Past_Papers"
        downloads_path.mkdir(parents=True, exist_ok=True)  # Create it if it doesn't exist
        return str(downloads_path)
    except Exception as e:
        print(f"Warning: Could not access Downloads folder: {e}")
        return "../Past_Papers"

DOWNLOAD_FOLDER: str = get_default_download_folder()

def get_config_path() -> str:
    """
    Returns the path to the configuration file.
    Uses APPDATA on Windows and ~/.config on other platforms.

    Returns:
        str: The path to the config.json file.
    """
    if platform.system() == "Windows":
        appdata = os.getenv('APPDATA')  # or LOCALAPPDATA for local-only config
        base = os.path.join(appdata, "EasyPastPapers")
        os.makedirs(base, exist_ok=True)
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "config.json")
CONFIG_PATH: str = get_config_path()
    
CONNECT_TIMEOUT: int = 5
READ_TIMEOUT: int = 15
MAX_PAGE_CACHE: int = 20 #Maximum number of HTML Pages to be cached
MAX_CONFIG_AGE: int = 60 * 60 * 24 * 28 # 1 month in seconds

# --- For getting the link extensions and subjects

# In between a and level, match any non-word character (i.e., symbol — not letter/digit/underscore)
ALEVEL_REGEX: str = r"a(?:[\W_]|%20)?level"
IGCSE_REGEX: str = r"(?:IGCSE|IG)"
OLEVEL_REGEX: str = r"o(?:[\W_]|%20)?level"

ALEVEL_PATTERN: re.Pattern = re.compile(ALEVEL_REGEX, re.IGNORECASE)
IGCSE_PATTERN: re.Pattern = re.compile(IGCSE_REGEX, re.IGNORECASE)
OLEVEL_PATTERN: re.Pattern = re.compile(OLEVEL_REGEX, re.IGNORECASE)

SESSION_LETTERS: list[str] = ["m", "s", "w", "y"] # m: Feb-March, s: May-June, w: Oct-Nov, y: Specimen

NON_SPECIMEN_PAPER_TYPES: set[str] = {"qp", "ms", "er", "gt", "sf", "in", "i2", "ci", "qr", "rp", "tn", "ir"}
SPECIMEN_PAPER_TYPES: set[str] = {"sc", "sci", "si" , "sm", "sp", "su", "sy"}

# 0620_y20-21_su
# 0580_y20-22_sy
PAPER_TYPES_WITHOUT_PAPER_NUM: set[str] = {"er", "gt", "sy", "su"}
PAPER_TYPES_WITH_2_YEARS: set[str] = {"sy", "su"} # can have 2 years but not mandatory

SUBJECT_CODE_REGEX: str = r"(\d{4})"
SESSION_LETTERS_STRING: str = "".join(SESSION_LETTERS)
SESSION_REGEX: str = rf"([{SESSION_LETTERS_STRING}])(\d{{2}}|\d{{2}}-\d{{2}})"
PAPER_TYPES_STRING: str = "|".join(SPECIMEN_PAPER_TYPES.union(NON_SPECIMEN_PAPER_TYPES))
PAST_PAPER_REGEX: str = rf"^{SUBJECT_CODE_REGEX}_{SESSION_REGEX}_({PAPER_TYPES_STRING})(?:_(\d[a-z0-9]?))?$"
PAST_PAPER_PATTERN: re.Pattern = re.compile(PAST_PAPER_REGEX, re.IGNORECASE)

SESSION_MAP: dict[str, str] = {
    "m" : "Feb-March",
    "s" : "May-June",
    "w" : "Oct-Nov",
    "y" : "Specimen"
}