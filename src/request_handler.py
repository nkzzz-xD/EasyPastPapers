import requests
from constants import *
from requests.exceptions import HTTPError, ConnectionError
from bs4 import BeautifulSoup
from bs4 import FeatureNotFound

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
