import requests
from constants import *
from requests.exceptions import HTTPError, ConnectionError
from bs4 import BeautifulSoup
from bs4 import FeatureNotFound
import os
import sys
import time

download_file = None
download_file_expected_size = 0

def download_with_progress(url, base_url, download_folder, file_name, log_errors = True):
    global download_file
    global download_file_expected_size
    download_file = download_folder + "/" + file_name
    try:
        with requests.get(url, stream = True, timeout = (CONNECT_TIMEOUT, READ_TIMEOUT)) as response:
            response.raise_for_status()
            download_file_expected_size = int(response.headers.get('content-length', 0))
            chunk_size = 8192 # Read in 8KB chunks
            downloaded = 0
            update_threshold = 64 * 1024 # Update the percentage every 64KB
            update_interval = 0.5 # Have an update interval so the download does not appear frozen on very slow connections.\
            last_update_time = time.time()
            progressed_bytes = 0

            os.makedirs(download_folder, exist_ok = True)
            if os.path.exists(download_file):
                user_response = None
                while (not user_response) or user_response.lower() != "y" or user_response.lower() != "n":
                    user_response = input(f"File at path '{download_file}' already exists. Do you want to overwrite this?\n[Y for yes and N for no]\n") #TODO Imporve the 
                    if user_response.lower() == "n":
                        print(f"Download of file '{download_file}' cancelled.")
                        return True
                    elif user_response.lower() == "y":
                        break
                
            #TODO Ad a flag to ignore files that already exist
            with open(download_file, 'wb') as f:
                sys.stdout.write('\x1b[1A')  # Move cursor up
                for chunk in response.iter_content(chunk_size = chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progressed_bytes += len(chunk)
                        now = time.time()
                        if progressed_bytes >= update_threshold or now - last_update_time >= update_interval:
                            percent = (downloaded / download_file_expected_size) * 100 if download_file_expected_size else 0
                            sys.stdout.write('\x1b[2K')  # Clear entire line
                            sys.stdout.write(f"\r📥 Downloading {file_name}... ({int(percent):d})%")
                            sys.stdout.flush() 
                            progressed_bytes = 0
                            last_update_time = now
            sys.stdout.write('\x1b[2K')  # Clear entire line 
            sys.stdout.write(f"\r✅{GREEN} File saved to: {os.path.abspath(download_file)}{RESET}\n")
            sys.stdout.flush()
            download_file = None
            download_file_expected_size = 0
            return True
    except ConnectionError as conn_err:
        if not log_errors:
            return
        sys.stdout.write('\x1b[2K')
        print(f"\r❌{RED} Connection error while downloading {url}:{RESET} {str(conn_err)}\n{YELLOW}Make sure you are connected to the internet.{RESET}")
        return False
    except HTTPError as http_err:
        if not log_errors:
            return
        sys.stdout.write('\x1b[2K')
        print(f"\r❌{RED} HTTP error downloading:{RESET} {str(http_err)}\n{YELLOW}This paper might not be on {base_url}{RESET}")
        return False
    except (PermissionError, FileNotFoundError, OSError) as file_err:
        sys.stdout.write('\x1b[2K')
        print(f"\r❌{RED} File system error:{RESET} {file_err}")
        return False 
    except Exception as err:
        sys.stdout.write('\x1b[2K')
        print(f"\r❌{RED} Unexpected error occured while downloading:{RESET} {str(err)}")
        return False
    
    finally:
        delete_incomplete_download()

def delete_incomplete_download():
    # Check if download completed
    if (not download_file) or (not os.path.exists(download_file)) or os.path.getsize(download_file) >= download_file_expected_size:
        return
    try:
        os.remove(download_file)
    except Exception as cleanup_err:
        #Shouldn't ever really happen
        print(f"{RED}Failed to clean up partial file:{RESET} {cleanup_err}")

def safe_get_response(url, print_output = True):
    try:
        response = requests.get(url, timeout = (CONNECT_TIMEOUT, READ_TIMEOUT))
        response.raise_for_status()
        return response
    except ConnectionError as conn_err:
        if not print_output:
            return
        print(f"{RED}Error connecting to {url}:{RESET} {str(conn_err)}\n{YELLOW}Make sure you are connected to the internet.{RESET}")
    except HTTPError as http_err:
        if not print_output:
            return
        print(f"{RED}HTTP error occured:{RESET} {str(http_err)}")
    except Exception as err:
        if not print_output:
            return
        print(f"{RED}Unexpected error occured:{RESET} {str(err)}")
    
def get_response(url):
    response = safe_get_response(url)
    if not response:
        raise SystemExit(1)
    return response

def safe_get_html(url, print_output = True):
    try:
        response = safe_get_response(url, print_output)
        if not response:
            return None
        response.encoding = "utf-8"
        return BeautifulSoup(response.text, 'html.parser') # Parse the text as html
    except FeatureNotFound as parser_err:
        if not print_output:
            return
        print(f"{RED}HTML parser not found:{RESET} {parser_err}")
    except Exception as err:
        if not print_output:
            return
        print(f"{RED}Error while parsing HTML:{RESET} {err}")

def get_html(url):
    html = safe_get_html(url)
    if not html:
        raise SystemExit(1)
    return html