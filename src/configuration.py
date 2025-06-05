import json
import re
from requesthandler import get_html
from constants import *
import time
import sys
from utils import print_error, program_exit

class Configuration:
    CONFIG_PATH = "config.json"
    base_url = BASE_URL
    download_folder = DOWNLOAD_FOLDER
    connect_timeout = CONNECT_TIMEOUT
    read_timeout = READ_TIMEOUT
    max_page_cache = MAX_PAGE_CACHE
    exam_page_links = {}
    subjects = {}

    @classmethod
    def load_config(cls):
        try:
            with open(Configuration.CONFIG_PATH, "r") as f:
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
    def store_config(cls):
        html_page = get_html(cls.base_url, (cls.connect_timeout, cls.read_timeout))
        exam_page_links = find_link_extensions(html_page)
        subjects = find_subjects(cls, cls.base_url, exam_page_links)
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
            with open(cls.CONFIG_PATH, "w") as f:
                json.dump(config_json, f, indent= 4, ensure_ascii = False)
        except OSError:
            print(f"{RED}Fatal: Could not save configuration file.{RESET}")
            raise SystemExit(1)
        

def find_link_extensions(html_page):
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
    # for key, value in link_extension_dict.items():
    #     if value is None:
    #         print_error(f"Could not find {key} exam links", f"\nMake sure you are connected to the internet and try again. Check the base url in the configuration is correct.")
    #         program_exit()
    return link_extension_dict

def find_subjects(cls, url, link_extensions):
    subjects_map_all_exams = {} #Key is exam (igcse, o level or alevel), value is a dict of subject codes to the link to the subject page.
    for key, value in link_extensions.items():
        subjects_map = {}
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

# def find_specimen_page(url):