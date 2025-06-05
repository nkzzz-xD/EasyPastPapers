from requesthandler import *
import re
import cmd
import shlex
import os
from utils import * 
from cache import *
import datetime

class EasyPaperShell(cmd.Cmd):
    
    intro = "Welcome to Easy Past Papers. Type help or ? to list commands."

    prompt = f"{CYAN}Enter a command> {RESET}"

    GET_USAGE = f"Usage: {YELLOW}get (paper code) [-o/--open] [-f/--force] [-s/--skip-existing] [-ns/--no-session-folders]{RESET}"
    PAPER_CODE_EXAMPLE = f"Paper code must be in the format: {YELLOW}(4-digit subject code){RESET}_{YELLOW}(session code)(2 digit year code){RESET}_{YELLOW}(paper type){RESET}_{YELLOW}(optional paper identifier){RESET}\
        \nPaper identifier can be a 1 or 2 digit number or a digit followed by a letter.\
        \nExample: {YELLOW}get 0452_w04_qp_3{RESET}"
    
    GET_MANY_USAGE = f"Usage: {YELLOW}getmany (subject code) (range) [-f/--force] [-s/--skip-existing] [-ns/--no-session-folders]{RESET}\
                     \nRange can be a single session code, a range of years, or a combination of both.\
                     \nRange can be in the format:\
                     \n{YELLOW}(session letter)(2 digit year code){RESET}\
                     \n{YELLOW}(session letter)(2 digit year code){RESET}-{YELLOW}(2 digit year code){RESET}\
                     \n{YELLOW}(2 digit year code){RESET}-{YELLOW}(2 digit year code){RESET}"
    GET_MANY_EXAMPLE = f"Example: {YELLOW}getmany 0452 14-17{RESET}"

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.page_cache = PageCache() # Use this in order to enforce max size for cache pool
        self.max_cache_size = config.max_page_cache
    
    def do_get(self, arg):
        """Download a specific paper.\n{USAGE}\
        \nNote: {PAPER_CODE_EXAMPLE} {YELLOW}-o -f{RESET}\
        \nOptional flags:\
        \n-o / --open flag: open file after download.\
        \n-f / --force flag: download the file without asking for confirmation if it already exists.\
        \n                   Re-downloads files which already exist in the download folder.\
        \n-s / --skip-existing flag: skip downloading the file if it already exists in the download folder.\
        \n-ns / --no-session-folders flag: do not create session folders in the download folder.\
        \nDo NOT include the file extension."""
        args = shlex.split(arg)
        file_name = args[0] if args else None
        expected_flags = [("-o", "--open"),
                           ("-f", "--force"),
                           ("-s", "--skip-existing"),
                           ("-ns", "--no-session-folders")]
        args = [s.lower() for s in args] # Make all args lowercase to avoid case sensitivity issues
        if not file_name:
            print_error("Please specify a file to download", "\n" + EasyPaperShell.GET_USAGE)
            return
        if not check_args("get", 1, args, expected_flags, [(1,2)], EasyPaperShell.GET_USAGE):
            return
        open_after = (expected_flags[0][0] in args) or (expected_flags[0][1] in args)
        force_download = (expected_flags[1][0] in args) or (expected_flags[1][1] in args)
        skip_existing =  (expected_flags[2][0] in args) or  (expected_flags[2][1] in args)
        session_folders = not (expected_flags[3][0] in args or expected_flags[3][1] in args) # If the user specifies -ns or --no-session-folders, we will not create session folders
        force_download = force_download if force_download else not skip_existing if skip_existing else None # If force_download is None, it means that the user did not specify any flags
        download_paper(self, file_name, open_after, force_download, session_folders)

    def help_get(self):
        """Manually print the help text for 'get' with color support."""
        print(self.do_get.__doc__.format(YELLOW=YELLOW, RESET=RESET, USAGE=EasyPaperShell.GET_USAGE, PAPER_CODE_EXAMPLE=EasyPaperShell.PAPER_CODE_EXAMPLE))

    def do_getmany(self, arg):
        """Download all past papers for a given range.\n{USAGE}\
        \n{GET_MANY_EXAMPLE} -o -f{RESET}\
        \nOptional flags:\
        \n-f / --force flag: download the files without asking for confirmation if they already exist.\
        \n                   Re-downloads files which already exist in the download folder.\
        \n-s / --skip-existing flag: skip downloading the files if they already exist in the download folder.\
        \n-ns / --no-session-folders flag: do not create session folders in the download folder."""
        args = shlex.split(arg)
        subject_code = args[0] if args else None
        range = args[1] if len(args) > 1 else None
        expected_flags = [ ("-f", "--force"),
                           ("-s", "--skip-existing"),
                           ("-ns", "--no-session-folders")]
        args = [s.lower() for s in args]
        if not subject_code:
            print_error("Please specify a subject code", "\n" + EasyPaperShell.GET_MANY_USAGE)
            return
        if not range:
            print_error("Please specify a range", "\n" + EasyPaperShell.GET_MANY_USAGE)
            return
        range = range.lower()
        if not check_args("getmany", 2, args, expected_flags, [(0,1)], EasyPaperShell.GET_MANY_USAGE):
            return
        if not re.match(f"^{SUBJECT_CODE_REGEX}$", subject_code):
            print_error(f"Invalid subject code {YELLOW}'{subject_code}'{RED} as parameter to getrange",
                        f"\nSubject code must be a 4 digit number.", 
                        EasyPaperShell.GET_MANY_USAGE)
            return
        
        single_session_range_match = re.match(r"^([msw])(\d{2})-(\d{2})$", range)
        range_match = re.match(r"^(\d{2})-(\d{2})$", range)
        session_letters = "".join(SESSION_LETTERS)
        single_session_match = re.match(rf"^([{session_letters}])(\d{{2}})$", range)
        single_year_match = re.match(r"^(\d{2})$", range)

        # Determine sessions to download
        sessions_to_download = []
        current_year = datetime.datetime.now().year % 100

        if single_session_range_match:
            session, start_year, end_year = single_session_range_match.groups()
            start_year = int(start_year)
            end_year = int(end_year)
            if end_year < start_year:
                print_error("End year must be greater than or equal to start year", None, EasyPaperShell.GET_MANY_USAGE)
                return
            if 0 >= start_year or end_year > current_year:
                print_error(f"Year {YELLOW}'{year}'{RED} is out of valid range {YELLOW}(1 to {current_year}){RESET}")
                return
            sessions_to_download = [f"{session}{year:02d}" for year in range(start_year, end_year + 1)]

        elif range_match:
            start_year, end_year = map(int, range_match.groups())
            if end_year < start_year:
                print_error("End year must be greater than or equal to start year", None, EasyPaperShell.GET_MANY_USAGE)
                return
            if 0 >= start_year or end_year > current_year:
                print_error(f"Year {YELLOW}'{year}'{RED} is out of valid range {YELLOW}(1 to {current_year}){RESET}")
                return
            for year in range(start_year, end_year + 1):
                for session in SESSION_LETTERS:
                    sessions_to_download.append(f"{session}{year:02d}")

        elif single_session_match:
            session, year = single_session_match.groups()
            year = int(year)
            if 0 >= year or year > current_year:
                print_error(f"Year {YELLOW}'{year}'{RED} is out of valid range {YELLOW}(1 to {current_year}){RESET}")
                return
            sessions_to_download = [range]
        elif single_year_match:   
            year = int(single_year_match.group(1))
            for session in SESSION_LETTERS:
                sessions_to_download.append(f"{session}{year:02d}")
        else:
            print_error(f"Invalid range {YELLOW}'{range}'{RED}", None, EasyPaperShell.GET_MANY_USAGE + "\n" + EasyPaperShell.GET_MANY_EXAMPLE)
            return
        subject_link = None
        subject_exam = None
        for key, value in self.config.subjects.items():
            if subject_code in value.keys():
                subject_link = value[subject_code]
                subject_exam = key
                break
            
        if not subject_link:
            print_error(f"Unknown subject code {YELLOW}'{subject_code}'{RESET}")
            return
        
        force_download = (expected_flags[0][0] in args) or (expected_flags[0][1] in args)
        skip_existing = (expected_flags[1][0] in args) or (expected_flags[1][1] in args)
        session_folders = not (expected_flags[2][0] in args or expected_flags[2][1] in args) # If the user specifies -ns or --no-session-folders, we will not create session folders
        force_download = force_download if force_download else not skip_existing if skip_existing else None # If force_download is None, it means that the user did not specify any flags
        
        total_downloaded = 0
        total_skipped = 0
        for range in sessions_to_download:
            print(f"\rPreparing for download of all past papers for {YELLOW}'{subject_code}'{RESET} in range {YELLOW}'{range}'{RESET}...")
            session = range[0]
            year = range[1:]
            link_for_subject = self.config.base_url + "/" + self.config.exam_page_links[subject_exam] + "/" + self.config.subjects[subject_exam][subject_code]
            paper_year_on_site = "Specimen Papers" if session == "y" else "20" + year
            link_for_year = link_for_subject + "/" + paper_year_on_site
            session_folder = f"/{SESSION_MAP[session]}" if session_folders else ""
            download_folder = f"{self.config.download_folder}/{self.config.subjects[subject_exam][subject_code]}/{paper_year_on_site}{session_folder}"

            # Get the key for retrieving the html page for the year from the cache.
            # If the session is specimen, we will use the session as the key, otherwise we will use the year.
            if session == "y":
                cache_key = (subject_code, session)
            else:
                cache_key = (subject_code, year)

            if cache_key in self.page_cache:
                html_for_year = self.page_cache.get(cache_key) # Get the html from the cache if present.
            else:
                html_for_year = safe_get_html(link_for_year, False)
                if not html_for_year:
                    link_for_year = link_for_subject
                    html_for_year = get_html(link_for_year, False if session == "y" else True)
                # To add to the cache
                self.page_cache[cache_key] = html_for_year

            successful_downloads = 0
            skipped = 0
            links = html_for_year.find_all('a')
            for link in links:
                link_str = link.get('href')
                if (re.search(range, link_str)):
                    file_name = link_str.strip("/") # Get the file name from the link
                    content_response = download_with_progress(link_for_year + "/" + file_name, 
                                                    self.config.base_url,
                                                    download_folder,
                                                    file_name,
                                                    force_download)
                    if content_response == FILE_DOWNLOADED:
                        successful_downloads += 1
                        total_downloaded += 1
                        print("\r")
                    elif content_response == FILE_EXISTS:
                        skipped += 1
                        total_skipped += 1
            if successful_downloads > 0:
                print(f"✅{GREEN} Successfully downloaded {successful_downloads} past paper{'s' if successful_downloads > 1 else ''} for {YELLOW}'{self.config.subjects[subject_exam][subject_code]}'{GREEN} in session {YELLOW}'{range}'{GREEN} to {YELLOW}'{os.path.abspath(download_folder)}'{RESET}")
            elif skipped == 0:
                sys.stdout.write('\x1b[1A')
                sys.stdout.write('\x1b[2K')
                sys.stdout.flush()
                print_error(f"Could not find any past papers for {YELLOW}'{self.config.subjects[subject_exam][subject_code]}'{RED} in session {YELLOW}'{range}'{RESET}",
                            f"\nMay not be available on {YELLOW}{self.config.base_url}{RESET} or the session code does not exist.\
                            \nMake sure you have entered the correct subject code and session code.",
                            EasyPaperShell.GET_MANY_USAGE, True)
        if total_downloaded == 0 and total_skipped == 0:
            print_error(f"No past papers could be downloaded for {YELLOW}'{self.config.subjects[subject_exam][subject_code]}'{RED} in the given session/range", None, None, True)
        
    def help_getmany(self):
        """Manually print the help text for 'getmany' with color support."""
        print(self.do_getmany.__doc__.format(YELLOW=YELLOW, RESET=RESET, USAGE=EasyPaperShell.GET_MANY_USAGE, GET_MANY_EXAMPLE = EasyPaperShell.GET_MANY_EXAMPLE))

    def default(self, line):
        print_error(f"Unknown command: {YELLOW}'{line}'{RED}")

    def do_exit(self, arg):
        """Exit the program."""
        program_exit()

def check_args(function_name, expected_length, args, expected_flags=[], mutally_exclusive_flags=[], usage_string=None):
    arg_count = 0
    invalid_flags = set({})
    expected_flags_unpacked = [element for tuple_item in expected_flags for element in tuple_item]
    for arg in args:
        if not arg.startswith("-"):
            arg_count += 1
            continue
        if len(arg) == 1:
            arg_count += 1
            continue
        if arg not in expected_flags_unpacked:
            invalid_flags.add(arg)

    if arg_count != expected_length:
        print_error(f"Unexpected number of (non-flag) arguments passed to {YELLOW}{function_name}{RED} command", 
                    f"\nExpected {YELLOW}{expected_length}{RESET} but was {YELLOW}{arg_count}{RESET}",
                    usage_string)
        return False
    if invalid_flags:
        invalid_flags_joined = f"'{RED}, {YELLOW}'".join(invalid_flags)
        invalid_plural_s = "s" if len(invalid_flags) > 1 else ""
        expected_plural_s = "s" if len(expected_flags) > 1 else ""
        expected_flags_joined = f"'{RESET}, {YELLOW}'".join(expected_flags_unpacked)
        print_error(f"Unexpected flag{invalid_plural_s} {YELLOW}'{invalid_flags_joined}'{RED} encountered", 
                    f"\n{YELLOW}{function_name}{RESET} command takes " +
                    f"only {YELLOW}'{expected_flags_joined}'{RESET} flag{expected_plural_s}." if len(expected_flags_unpacked) > 0 else "no flags.",
                    usage_string)
        return False
    if len(mutally_exclusive_flags) > 0:
        for tuple_item in mutally_exclusive_flags:
            comparison_flags = (expected_flags[tuple_item[0]], expected_flags[tuple_item[1]])
            flag1 = comparison_flags[0][0] if comparison_flags[0][0] in args else comparison_flags[0][1] if comparison_flags[0][1] in args else None
            flag2 = comparison_flags[1][0] if comparison_flags[1][0] in args else comparison_flags[1][1] if comparison_flags[1][1] in args else None
            if flag1 and flag2:
                print_error(f"Mutually exclusive flags {YELLOW}'{flag1}'{RED} and {YELLOW}'{flag2}'{RED} cannot be used together",
                            None,
                            usage_string)
                return False
    return True

def download_paper(shell, file_name, open_after, force_download, session_folders):
    """Download a specific past paper based on the file name provided."""
    match = PAST_PAPER_PATTERN.search(file_name)
    if not match:
        print_error(f"Invalid file {YELLOW}'{file_name}'{RED} as parameter to get",
        f"\nEnter a valid file name.\n{EasyPaperShell.PAPER_CODE_EXAMPLE}")
        return
    subject_code, session, year, paper_type, paper_num = match.groups()
    session = session.lower()
    paper_type = paper_type.lower()

    subject_link = None
    subject_exam = None
    for key, value in shell.config.subjects.items():
        if subject_code in value.keys():
            subject_link = value[subject_code]
            subject_exam = key
            break
        
    if not subject_link:
        print_error(f"Unknown subject code {YELLOW}'{subject_code}'{RESET}")
        return
    
    if session == "y" and paper_type not in SPECIMEN_PAPER_TYPES:
        specimen_paper_types_joined = f"'{RESET}, {YELLOW}'".join(SPECIMEN_PAPER_TYPES)
        print_error(f"Invalid file {YELLOW}'{file_name}'{RED} as parameter to get",
                    f"\nSpecimen paper cannot have paper type {YELLOW}'{paper_type}'{RESET}\
                    \nMust be one of {YELLOW}'{specimen_paper_types_joined}'{RESET}.\
                    \nEnter a valid file.")
        return
    
    if session != "y" and paper_type in SPECIMEN_PAPER_TYPES:
        non_specimen_paper_types_joined = f"'{RESET}, {YELLOW}'".join(NON_SPECIMEN_PAPER_TYPES)
        print_error(f"Invalid file {YELLOW}'{file_name}'{RED} as parameter to get",
                    f"\nNon specimen paper cannot have paper type {YELLOW}'{paper_type}'{RESET}\
                    \nMust be one of {YELLOW}'{non_specimen_paper_types_joined}'{RESET}.\
                    \nEnter a valid file.")
        return

    if paper_type not in PAPER_TYPES_WITHOUT_PAPER_NUM and not paper_num:
        print_error(f"Invalid file {YELLOW}'{file_name}'{RED} as parameter to get",
                    f"\nPaper of type {YELLOW}'{paper_type}'{RESET} must have paper number.")
        return
    
    if paper_type in PAPER_TYPES_WITHOUT_PAPER_NUM and paper_num:
        print_error(f"Invalid file {YELLOW}'{file_name}'{RED} as parameter to get",
                    f"\nPaper of type {YELLOW}'{paper_type}'{RESET} cannot have paper number.")
        return
    
    if paper_type not in PAPER_TYPES_WITH_2_YEARS and re.search(r"\d{2}-\d{2}", year):
        two_year_paper_types_joined = f"'{RESET}, {YELLOW}'".join(PAPER_TYPES_WITH_2_YEARS)
        print(f"Invalid file {YELLOW}'{file_name}'{RED} as parameter to get",
              f"\nPaper of type {YELLOW}'{paper_type}'{RESET} must not have a range of years.\
                \nMust be one of {YELLOW}'{two_year_paper_types_joined}'{RESET}.")
        return
    
    print(f"\rPreparing for download of {file_name}...")

    link_for_subject = shell.config.base_url + "/" + shell.config.exam_page_links[subject_exam] + "/" + shell.config.subjects[subject_exam][subject_code]
    paper_year_on_site = "Specimen Papers" if session == "y" else "20" + year
    link_for_year = link_for_subject + "/" + paper_year_on_site
    pdf_link_prediction = link_for_year + "/" + file_name + ".pdf" # Most files will be pdfs so for efficiency we will try to download the pdf first
    session_folder = f"/{SESSION_MAP[session]}" if session_folders else ""
    download_folder = f"{shell.config.download_folder}/{shell.config.subjects[subject_exam][subject_code]}/{paper_year_on_site}{session_folder}"

    content_response = download_with_progress(pdf_link_prediction, 
                                                shell.config.base_url, #For error message purposes
                                                download_folder,
                                                file_name + ".pdf",
                                                force_download,
                                                False)
    if content_response != FAILED_TO_DOWNLOAD:
        if open_after:
            open_file(download_folder + "/"+ file_name + ".pdf")
        return
    
    # Get the key for retrieving the html page for the year from the cache.
    # If the session is specimen, we will use the session as the key, otherwise we will use the year.
    if session == "y":
        cache_key = (subject_code, session)
    else:
        cache_key = (subject_code, year)

    if cache_key in shell.page_cache:
        html_for_year = shell.page_cache.get(cache_key) # Get the html from the cache if present.
    else:
        html_for_year = safe_get_html(link_for_year, False)
        if not html_for_year:
            link_for_year = link_for_subject
            html_for_year = get_html(link_for_year)
        # To add to the cache
        shell.page_cache[cache_key] = html_for_year

    # Get the links for papers for that year.
    links = html_for_year.find_all('a')
    found_file_name = None
    for link in links:
        link_str = link.get('href')
        # now to find the file with the regex
        if (re.search(file_name, link_str)):
            # To get the link to the requested paper.
            found_file_name = link_str.strip("/")
            break
    if not found_file_name:
        print_error(f"Could not find file {YELLOW}'{file_name}'{RED} on {YELLOW}'{shell.config.base_url}'{RESET}")
        return
    
    # If the file is found, we will download it.
    content_response = download_with_progress(link_for_year + "/" + found_file_name, 
                                                shell.config.base_url,
                                                download_folder,
                                                file_name,
                                                force_download)
    if content_response != FAILED_TO_DOWNLOAD and open_after:
        open_file(download_folder + "/"+ file_name)