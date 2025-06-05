import re
from pathlib import Path
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[36m"
GREEN = "\033[92m"
RESET = "\033[0m"
BASE_URL = "https://papers.gceguide.cc"
from pathlib import Path

def get_default_download_folder():
    try:
        # Attempt to use the user's Downloads folder
        downloads_path = Path.home() / "Downloads" / "Past_Papers"
        downloads_path.mkdir(parents=True, exist_ok=True)  # Create it if it doesn't exist
        return str(downloads_path)
    except Exception as e:
        print(f"Warning: Could not access Downloads folder: {e}")
        return "../Past_Papers"

DOWNLOAD_FOLDER = get_default_download_folder()
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 15
MAX_PAGE_CACHE = 20 #Maximum number of HTML Pages to be cached
MAX_CONFIG_AGE = 60 * 60 * 24 * 28 # 1 month in seconds
# --- For getting the link extensions and subjects
# In between a and level, match any non-word character (i.e., symbol — not letter/digit/underscore)
ALEVEL_REGEX = r"a(?:[\W_]|%20)?level"
IGCSE_REGEX = r"(?:IGCSE|IG)"
OLEVEL_REGEX = r"o(?:[\W_]|%20)?level"

ALEVEL_PATTERN = re.compile(ALEVEL_REGEX, re.IGNORECASE)
IGCSE_PATTERN = re.compile(IGCSE_REGEX, re.IGNORECASE)
OLEVEL_PATTERN = re.compile(OLEVEL_REGEX, re.IGNORECASE)
# ---
SESSION_LETTERS = ["m", "s", "w", "y"] # m: Feb-March, s: May-June, w: Oct-Nov, y: Specimen
NON_SPECIMEN_PAPER_TYPES = {"qp", "ms", "er", "gt", "sf", "in", "i2", "ci", "qr", "rp", "tn", "ir"}
SPECIMEN_PAPER_TYPES = {"sc", "sci", "si" , "sm", "sp", "su", "sy"}
# 0620_y20-21_su
# 0580_y20-22_sy
PAPER_TYPES_WITHOUT_PAPER_NUM = {"er", "gt", "sy", "su"}
PAPER_TYPES_WITH_2_YEARS = {"sy", "su"} # can have 2 years but not mandatory
SUBJECT_CODE_REGEX = r"(\d{4})"
SESSION_LETTERS_STRING = "".join(SESSION_LETTERS)
SESSION_REGEX = rf"([{SESSION_LETTERS_STRING}])(\d{{2}}|\d{{2}}-\d{{2}})"
PAPER_TYPES_STRING = "|".join(SPECIMEN_PAPER_TYPES.union(NON_SPECIMEN_PAPER_TYPES))
PAST_PAPER_REGEX = rf"^{SUBJECT_CODE_REGEX}_{SESSION_REGEX}_({PAPER_TYPES_STRING})(?:_(\d[a-z0-9]?))?$"
PAST_PAPER_PATTERN = re.compile(PAST_PAPER_REGEX, re.IGNORECASE)
SESSION_MAP = {
    "m" : "Feb-March",
    "s" : "May-June",
    "w" : "Oct-Nov",
    "y" : "Specimen"
}