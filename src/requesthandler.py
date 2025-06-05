import requests
from constants import *
from utils import print_error
from requests.exceptions import HTTPError, ConnectionError
from bs4 import BeautifulSoup
from bs4 import FeatureNotFound
import os
import sys
import time

download_file = None
download_file_expected_size = 0

FILE_DOWNLOADED = 0
FAILED_TO_DOWNLOAD = 1
FILE_EXISTS = 2

def download_with_progress(url, base_url, download_folder, file_name, force_download, log_errors = True):
    global download_file
    global download_file_expected_size
    download_file = download_folder + "/" + file_name
    abs_download_path = os.path.abspath(download_file)
    os.makedirs(download_folder, exist_ok = True)
    if os.path.exists(download_file) and not force_download:
        user_response = None
        if force_download is not None: #This means force download was purposefully set to False
            print(f"\r{YELLOW}File already exists at path '{abs_download_path}'; cancelling download. Use -f or --force to overwrite.{RESET}")
            return FILE_EXISTS
        while (not user_response) or user_response.lower() != "y" or user_response.lower() != "n":
            print(f"\rFile at path {YELLOW}'{abs_download_path}'{RESET} already exists.")
            user_response = input("\rDo you want to overwrite this? [Y for yes and N for no]: ")
            if user_response.lower() == "n":
                sys.stdout.write('\x1b[1A')
                sys.stdout.write('\x1b[2K')
                sys.stdout.write('\x1b[1A')
                sys.stdout.write('\x1b[2K')
                sys.stdout.flush()
                print(f"\rDownload of file to {YELLOW}'{abs_download_path}'{RESET} cancelled as it already exists.")
                return FILE_EXISTS
            elif user_response.lower() == "y":
                break
    try:
        with requests.get(url, stream = True, timeout = (CONNECT_TIMEOUT, READ_TIMEOUT)) as response:
            response.raise_for_status()
            download_file_expected_size = int(response.headers.get('content-length', 0))
            chunk_size = 8192 # Read in 8KB chunks
            downloaded = 0
            update_threshold = 64 * 1024 # Update the percentage every 64KB
            update_interval = 0.5 # Have an update interval so the download does not appear frozen on very slow connections.
            last_update_time = time.time()
            progressed_bytes = 0
                
            with open(download_file, 'wb') as f:
                sys.stdout.write('\x1b[1A')  # Move cursor up
                sys.stdout.write('\x1b[2K')
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
            sys.stdout.write(f"\r✅{GREEN} {file_name} saved to: {abs_download_path}{RESET}\n")
            sys.stdout.flush()
            download_file = None
            download_file_expected_size = 0
            return FILE_DOWNLOADED
    except ConnectionError as conn_err:
        if not log_errors:
            return FAILED_TO_DOWNLOAD
        sys.stdout.write('\x1b[2K')
        print_error(f"Connection error while downloading {YELLOW}{url}{RED}", f"\n{conn_err}\n{YELLOW}Make sure you are connected to the internet.{RESET}")
        return FAILED_TO_DOWNLOAD
    except HTTPError as http_err:
        if not log_errors:
            return FAILED_TO_DOWNLOAD
        sys.stdout.write('\x1b[2K')
        print_error("HTTP error downloading", f"\n{http_err}\n{YELLOW}This paper might not be on {base_url}{RESET}")
        return FAILED_TO_DOWNLOAD
    except (PermissionError, FileNotFoundError, OSError) as file_err:
        sys.stdout.write('\x1b[2K')
        print_error("File system error", f"\n{file_err}")
        return FAILED_TO_DOWNLOAD 
    except Exception as err:
        sys.stdout.write('\x1b[2K')
        print_error("Unexpected error occured while downloading", f"\n{err}")
        return FAILED_TO_DOWNLOAD
    
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
        print_error("Failed to clean up partial file", f"\n{cleanup_err}")

def safe_get_response(url, print_output = True):
    try:
        response = requests.get(url, timeout = (CONNECT_TIMEOUT, READ_TIMEOUT))
        response.raise_for_status()
        return response
    except ConnectionError as conn_err:
        if not print_output:
            return
        print_error(f"Error connecting to {url}", f"\n{conn_err}\n{YELLOW}Make sure you are connected to the internet.{RESET}")
    except HTTPError as http_err:
        if not print_output:
            return
        print_error("HTTP error occured", f"\n{http_err}")
    except Exception as err:
        if not print_output:
            return
        print_error("Unexpected error occured", f"\n{err}")
    
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
        print_error("HTML parser not found", f"\n{parser_err}")
    except Exception as err:
        if not print_output:
            return
        print("Error while parsing HTML:", f"\n{err}")

def get_html(url, print_output = True):
    html = safe_get_html(url, print_output)
    if not html:
        raise SystemExit(1)
    return html

#TODO Add pydocs