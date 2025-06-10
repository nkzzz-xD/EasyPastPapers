import requests
from constants import *
from utils import print_error
from requests.exceptions import HTTPError, ConnectionError
from bs4 import BeautifulSoup
from bs4 import FeatureNotFound
import os
import sys
import time
from typing import Optional, Tuple

download_file: Optional[str] = None
download_file_expected_size: int = 0

FILE_DOWNLOADED: int = 0
FAILED_TO_DOWNLOAD: int = 1
FILE_EXISTS: int = 2

def download_with_progress(
    url: str,
    base_url: str,
    download_folder: str,
    file_name: str,
    force_download: Optional[bool],
    timeouts: Tuple[int, int],
    log_errors: bool = True
 ) -> int:
    """
    Downloads a file from the given URL with progress indication.

    Args:
        url (str): The URL to download from.
        base_url (str): The base URL (for error messages).
        download_folder (str): The folder to save the file in.
        file_name (str): The name of the file to save as.
        force_download (Optional[bool]): Whether to overwrite existing files. None means prompt the user.
        timeouts (Tuple[int, int]): (connect_timeout, read_timeout).
        log_errors (bool): Whether to print errors.

    Returns:
        int: FILE_DOWNLOADED, FILE_EXISTS, or FAILED_TO_DOWNLOAD.
    """
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
        with requests.get(url, stream = True, timeout = timeouts) as response:
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

def delete_incomplete_download() -> None:
    """
    Deletes an incomplete download file if the download did not finish.

    Returns:
        None
    """
    # Check if download completed
    if (not download_file) or (not os.path.exists(download_file)) or os.path.getsize(download_file) >= download_file_expected_size:
        return
    try:
        os.remove(download_file)
    except Exception as cleanup_err:
        # Shouldn't ever really happen
        print_error("Failed to clean up partial file", f"\n{cleanup_err}")

def safe_get_response(url: str, timeouts: Tuple[int, int], print_output: bool = True) -> Optional[requests.Response]:
    """
    Safely gets a response from a URL, handling exceptions.

    Args:
        url (str): The URL to request.
        timeouts (Tuple[int, int]): (connect_timeout, read_timeout).
        print_output (bool): Whether to print errors.

    Returns:
        Optional[requests.Response]: The response object, or None if failed.
    """
    try:
        response = requests.get(url, timeout = timeouts)
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
    
def get_response(url: str, timeouts: Tuple[int, int], print_output: bool = True) -> requests.Response:
    """
    Gets a response from a URL or exits if it fails.

    Args:
        url (str): The URL to request.
        timeouts (Tuple[int, int]): (connect_timeout, read_timeout).
        print_output (bool): Whether to print errors.

    Returns:
        requests.Response: The response object.

    Raises:
        SystemExit: If the request fails.
    """
    response = safe_get_response(url, timeouts, print_output)
    if not response:
        raise SystemExit(1)
    return response

def safe_get_html(url: str, timeouts: Tuple[int, int], print_output: bool = True) -> Optional[BeautifulSoup]:
    """
    Safely gets and parses HTML from a URL.

    Args:
        url (str): The URL to request.
        timeouts (Tuple[int, int]): (connect_timeout, read_timeout).
        print_output (bool): Whether to print errors.

    Returns:
        Optional[BeautifulSoup]: The parsed HTML, or None if failed.
    """
    try:
        response = safe_get_response(url, timeouts, print_output)
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

def get_html(url: str, timeouts: Tuple[int, int], print_output: bool = True) -> BeautifulSoup:
    """
    Gets and parses HTML from a URL or exits if it fails.

    Args:
        url (str): The URL to request.
        timeouts (Tuple[int, int]): (connect_timeout, read_timeout).
        print_output (bool): Whether to print errors.

    Returns:
        BeautifulSoup: The parsed HTML.

    Raises:
        SystemExit: If the request fails.
    """
    html = safe_get_html(url, timeouts, print_output)
    if not html:
        raise SystemExit(1)
    return html