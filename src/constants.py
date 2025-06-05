import re
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[36m"
GREEN = "\033[92m"
RESET = "\033[0m"
BASE_URL = "https://papers.gceguide.cc"
DOWNLOAD_FOLDER = "../Past_Papers"
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 15
MAX_PAGE_CACHE = 20 #Maximum number of HTML Pages to be cached
MAX_CONFIG_AGE = 60 * 60 * 24 * 28 # 1 month in seconds
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