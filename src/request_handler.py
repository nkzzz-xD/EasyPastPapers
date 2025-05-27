import requests
from constants import *
from requests.exceptions import HTTPError, ConnectionError
from bs4 import BeautifulSoup
from bs4 import FeatureNotFound
import re

def safe_get_response(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response
    except ConnectionError as conn_err:
        print(f"{RED}Error connecting to {url}:{RESET} {str(conn_err)}\n{YELLOW}Make sure you are connected to the internet.{RESET}")
        raise SystemExit(1)
    except HTTPError as http_err:
        print(f"{RED}HTTP error occured:{RESET} {str(http_err)}")
        raise SystemExit(1)
    except Exception as err:
        print(f"{RED}Some error occured:{RESET} {str(err)}")
        raise SystemExit(1)

def safe_get_html(url):
    try:
        response = safe_get_response(url)
        response.encoding = "utf-8"
        return BeautifulSoup(response.text, 'html.parser') # Parse the text as html
    except FeatureNotFound as parser_err:
        print(f"{RED}HTML parser not found:{RESET} {parser_err}")
        raise SystemExit(1)
    except Exception as err:
        print(f"{RED}Error while parsing HTML:{RESET} {err}")
        raise SystemExit(1)


def find_link_extensions(html_page):
    link_extension_dict = {"alevel" : None, "igcse" : None  , "olevel" : None}

    # In between a and level, match any non-word character (i.e., symbol — not letter/digit/underscore)
    alevel_regex = r"a(?:[\W_]|%20)?level"
    igcse_regex = r"(?:IGCSE|IG)"
    olevel_regex = r"o(?:[\W_]|%20)?level"

    alevel_pattern = re.compile(alevel_regex, re.IGNORECASE)
    igcse_pattern = re.compile(igcse_regex, re.IGNORECASE)
    olevel_pattern = re.compile(olevel_regex, re.IGNORECASE)

    links = html_page.find_all('a')
    for link in links:
        link_str = link.get('href')
        if alevel_pattern.search(link_str):
            #Must ensure there are no leading or trailing "/" characters to avoid any confusion.
            link_extension_dict["alevel"] = link_str.strip("/")
        elif igcse_pattern.search(link_str):
            link_extension_dict["igcse"] = link_str.strip("/")
        elif olevel_pattern.search(link_str):
            link_extension_dict["olevel"] = link_str.strip("/")
    return link_extension_dict

def find_subjects(url, link_extensions):
    subjects_map_all_exams = {} #Key is exam (igcse, o level, alevel), value is a dict of subject codes to the full name
    for key, value in link_extensions.items():
        subjects_map = {}
        subject_regex = r"(\d{4})"
        subject_pattern = re.compile(subject_regex)
        html_page = safe_get_html(url + "/" + value)
        links = html_page.find_all('a')
        for link in links:
            link_str = link.get("href")
            # link_str = "a (7383)"
            match = subject_pattern.search(link_str)
            if (match):
                subjects_map[match.group()] = link_str.strip("/")
            subjects_map_all_exams[key] = subjects_map
    return subjects_map_all_exams