import json
import re
from typing import Optional, Dict, Any
from requesthandler import get_html
from constants import *
import time
import sys

class Configuration:
    """
    Handles loading and storing configuration for EasyPastPapers.

    Attributes:
        base_url (str): The base URL for downloading papers.
        download_folder (str): The folder where papers are downloaded.
        connect_timeout (int): Timeout for establishing network connections.
        read_timeout (int): Timeout for reading data from network connections.
        max_page_cache (int): Maximum number of HTML pages to cache.
        exam_page_links (dict): Mapping of exam types to their page links.
        subjects (dict): Mapping of exam types to their subjects.
    """
    base_url: str = BASE_URL
    download_folder: str = DOWNLOAD_FOLDER
    connect_timeout: int = CONNECT_TIMEOUT
    read_timeout: int = READ_TIMEOUT
    max_page_cache: int = MAX_PAGE_CACHE
    exam_page_links: Dict[str, Optional[str]] = {}
    subjects: Dict[str, Dict[str, str]] = {}

    @classmethod
    def load_config(cls) -> None:
        """
        Loads configuration from the config file. If the config file is missing or incomplete,
        it regenerates and saves a new config file.

        Raises:
            SystemExit: If the configuration file cannot be saved.
        """
        try:
            with open(CONFIG_PATH, "r") as f:
                obj = json.load(f)
                cls.download_folder = obj.get("download_folder", DOWNLOAD_FOLDER)
                cls.base_url = obj.get("base_url", BASE_URL)
                cls.connect_timeout = obj.get("connect_timeout", CONNECT_TIMEOUT)
                cls.read_timeout = obj.get("read_timeout", READ_TIMEOUT)
                cls.max_page_cache = obj.get("max_page_cache", MAX_PAGE_CACHE)
                cls.exam_page_links = obj["exam_page_links"] # These 2 are not stored within the program so if missing must be generated.
                cls.subjects = obj["subjects"]
                
                last_updated = obj.get("last_updated", 0)
                current_time = time.time()
                if current_time - last_updated > MAX_CONFIG_AGE:
                    sys.stdout.write('\x1b[1A')  # Move cursor up
                    sys.stdout.write('\x1b[2K')  # Clear entire line
                    sys.stdout.flush()
                    print(f"\r{YELLOW}Config is stale - reloading...{RESET}")
                    cls.store_config()
        except (KeyError, FileNotFoundError):
            cls.store_config()

    @classmethod
    def store_config(cls, skip_reload: bool = False) -> None:
        """
        Stores the current configuration to the config file.

        Args:
            skip_reload (bool): If True, skips reloading exam page links and subjects.
        Raises:
            SystemExit: If the configuration file cannot be saved.
        """
        # Sometimes we don't want to reload the exam page links and subjects, e.g. when changing the download folder.
        if not skip_reload:
            html_page = get_html(cls.base_url, (cls.connect_timeout, cls.read_timeout))
            exam_page_links = find_link_extensions(html_page)
            subjects = find_subjects(cls, cls.base_url, exam_page_links)
        else:
            exam_page_links = cls.exam_page_links
            subjects = cls.subjects
        config_json = {
            "base_url" : cls.base_url,
            "download_folder" : cls.download_folder,
            "connect_timeout" : cls.connect_timeout,
            "read_timeout" : cls.read_timeout,
            "max_page_cache" : cls.max_page_cache,
            "exam_page_links" : exam_page_links, 
            "subjects" : subjects,
            "last_updated" : time.time()
        }
        cls.exam_page_links = exam_page_links
        cls.subjects = subjects
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(config_json, f, indent= 4, ensure_ascii = False)
        except OSError:
            print(f"{RED}Fatal: Could not save configuration file.{RESET}")
            sys.stdout.flush()
            import signal
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            time.sleep(1) # Allow time for the message to be seen (Can be removed if debugging)
            raise SystemExit(1)
        

def find_link_extensions(html_page: Any) -> Dict[str, Optional[str]]:
    """
    Finds the link extensions for each exam type from the HTML page.

    Args:
        html_page: BeautifulSoup object of the main page.

    Returns:
        dict: Mapping of exam types ('alevel', 'igcse', 'olevel') to their link extensions.
    """
    link_extension_dict = {"alevel" : None, "igcse" : None  , "olevel" : None}
    links = html_page.find_all('a')
    for link in links:
        link_str = link.get('href')
        if ALEVEL_PATTERN.search(link_str):
            #Must ensure there are no leading or trailing "/" characters to avoid any confusion.
            link_extension_dict["alevel"] = link_str.strip("/")
        elif IGCSE_PATTERN.search(link_str):
            link_extension_dict["igcse"] = link_str.strip("/")
        elif OLEVEL_PATTERN.search(link_str):
            link_extension_dict["olevel"] = link_str.strip("/")
    return link_extension_dict

def find_subjects(cls: Configuration, url: str, link_extensions: Dict[str, Optional[str]]) -> Dict[str, Dict[str, str]]:
    """
    Finds all subjects for each exam type.

    Args:
        cls: The Configuration class (for timeouts).
        url (str): The base URL.
        link_extensions (dict): Mapping of exam types to their link extensions.

    Returns:
        dict: Mapping of exam types to their subjects (subject code to subject page link).
    """
    subjects_map_all_exams = {} #Key is exam (igcse, o level or alevel), value is a dict of subject codes to the link to the subject page.
    for key, value in link_extensions.items():
        subjects_map: Dict[str, str] = {}
        subject_regex = SUBJECT_CODE_REGEX
        subject_pattern = re.compile(subject_regex)
        html_page = get_html(url + "/" + (value if value else ""), (cls.connect_timeout, cls.read_timeout))
        links = html_page.find_all('a')
        for link in links:
            link_str = link.get("href")
            match = subject_pattern.search(link_str)
            if (match):
                subjects_map[match.group()] = link_str.strip("/")
            subjects_map_all_exams[key] = subjects_map
    return subjects_map_all_exams