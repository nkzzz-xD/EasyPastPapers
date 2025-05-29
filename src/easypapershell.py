from requesthandler import *
import re
import cmd
import shlex
import os
import platform
from collections import OrderedDict

specimen_session = "y"
non_specimen_paper_types = {"qp", "ms", "er", "gt", "sf", "in", "i2", "ci", "qr", "rp", "tn" "ir"}
specimen_paper_types = {"sc", "sci", "si" , "sm", "sp", "su", "sy"}
# 0620_y20-21_su
# 0580_y20-22_sy
paper_types_without_paper_num = {"er", "gt", "sy", "su"}
paper_types_with_2_years = {"sy", "su"} # can have 2 years but not mandatory
past_paper_regex = rf"^(\d{{4}})_([msw{specimen_session}])(\d{{2}}|\d{{2}}-\d{{2}})_({"|".join(specimen_paper_types.union(non_specimen_paper_types))})(?:_(\d{{1,2}}[a-z]?))?$"
past_paper_pattern = re.compile(past_paper_regex, re.IGNORECASE)

class EasyPaperShell(cmd.Cmd):

    intro = "Welcome to Easy Past Papers. Type help or ? to list commands."

    prompt = f"{CYAN}Enter a command> {RESET}"
    #TODO Make more consistent error message
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.page_cache = OrderedDict()  # Use this in order to enforce max size
        self.max_cache_size = config.max_page_cache
    
    def do_get(self, arg):
        """Download a specific paper.\nUsage: get (paper code) [-o]\nExample: get 0452_w04_qp_3 -o
        -o flag (optional): open file after download
        Do NOT include the file extension."""
        args = shlex.split(arg)
        file_name = args[0] if args else None
        if not file_name:
            print("❌ Please specify a file to download.\nUsage: get (paper code) [-o]")
            return
        if not check_args("get", 1, args, {"o"}):
            return
        open_after = '-o' in args
        download_paper(self, file_name, open_after)

    def default(self, line):
        print(f"❌ Unknown command: '{line}'. Type 'help' to see available commands.")

    def do_exit(self, arg):
        program_exit()

def check_args(function_name, expected_length, args, expected_flags):
    arg_count = 0
    invalid_flags = set({})
    for arg in args:
        if not arg.startswith("-"):
            arg_count += 1
            continue
        if len(arg) == 1:
            arg_count += 1
            continue
        if arg[1:] not in expected_flags:
            invalid_flags.add(arg)
    if arg_count != expected_length:
        print(f"❌ {RED}Unexpected number of arguments passed to {YELLOW}{function_name}{RED} command.{RESET}\nExpected {YELLOW}{expected_length}{RESET} but was {YELLOW}{arg_count}{RESET}")
        return False
    if invalid_flags:
        print(f"❌ {RED}Unexpected flag{"s" if len(invalid_flags) > 1 else ""} '{"', '".join(invalid_flags)}' encountered.{RESET}\n{YELLOW}{function_name}{RESET} command takes only '-{", '-".join(expected_flags)}' flag{"s" if len(expected_flags) > 1 else ""}")
        return False
    return True

def download_paper(shell, file_name, open_after):
        match = past_paper_pattern.search(file_name)
        if not match:
            print(f"""❌ Invalid file '{file_name}' as parameter to get. Enter a valid file.\
            \nExpected format: {YELLOW}(4-digit subject code){RESET}_{YELLOW}(session code)(2 digit year code){RESET}_{YELLOW}(paper type){RESET}_{YELLOW}(paper identifier){RESET}\
            \nExample: {YELLOW}0606{RESET}_{YELLOW}s17{RESET}_{YELLOW}qp{RESET}_{YELLOW}22{RESET}""")
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
            print(f"❌ {RED}Unknown subject code '{subject_code}{RESET}'")
            return
        
        if session == specimen_session and paper_type not in specimen_paper_types:
            print(f"❌ Invalid file '{file_name}' as parameter to get. Specimen paper cannot have paper type '{paper_type}'.\nMust be one of '{"', ".join(specimen_paper_types)}'.\nEnter a valid file.")
            return
        
        if session != specimen_session and paper_type in specimen_paper_types:
            print(f"❌ Invalid file '{file_name}' as parameter to get. Non specimen paper cannot have paper type '{paper_type}'.\nMust be one of '{"', ".join(non_specimen_paper_types)}'.\nEnter a valid file.")
            return

        if paper_type not in paper_types_without_paper_num and not paper_num:
            print(f"❌ Paper of type '{paper_type}' must have paper number.")
            return
        
        if paper_type in paper_types_without_paper_num and paper_num:
            print(f"❌ Paper of type '{paper_type}' must not have paper number.")
            return
        
        if paper_type not in paper_types_with_2_years and re.search(r"\d{2}-\d{2}", year):
            print(f"❌ Paper of type '{paper_type}' must not have a range of years. \nMust be one of '{"', ".join(paper_types_with_2_years)}'.")
            return
        
        print("\rPreparing for download...")

        link_for_subject = shell.config.base_url + "/" + shell.config.exam_page_links[subject_exam] + "/" + shell.config.subjects[subject_exam][subject_code]
        paper_year_on_site = "Specimen Papers" if session == specimen_session else "20" + year #TODO Fix from being hard coded to "Specimen Papers"
        link_for_year = link_for_subject + "/" + paper_year_on_site
        pdf_link_prediction = link_for_year + "/" + file_name + ".pdf"
        download_folder = shell.config.download_folder + "/" + shell.config.subjects[subject_exam][subject_code] + "/" + paper_year_on_site
        content_response = download_with_progress(pdf_link_prediction, 
                                                  shell.config.base_url,
                                                  download_folder,
                                                  file_name + ".pdf",
                                                  False)
        if content_response:
            if open_after: 
                open_file(download_folder + "/"+ file_name + ".pdf")
            return
        
        # now to find the file with the regex
        if session == specimen_session:
            cache_key = (subject_code, session)
        else:
            cache_key = (subject_code, year)
        if cache_key in shell.page_cache:
            html_for_year = shell.page_cache.get(cache_key)
            shell.page_cache.move_to_end(cache_key)
        else:
            html_for_year = safe_get_html(link_for_year, True)
            if not html_for_year:
                link_for_year = link_for_subject
                html_for_year = safe_get_html(link_for_year)

            # To add to the cache
            shell.page_cache[cache_key] = html_for_year
            if len(shell.page_cache) > shell.max_cache_size:
                shell.page_cache.popitem(last = False)

        # Get the links for papers for that year.
        links = html_for_year.find_all('a')
        for link in links:
            link_str = link.get('href')
            if (re.search(file_name, link_str)):
                # To get the link to the requested paper.
                file_name = link_str.strip("/")
                break

        
        content_response = download_with_progress(link_for_year + "/" + file_name, 
                                                  shell.config.base_url,
                                                  download_folder,
                                                  file_name)
        if not content_response:
            return

        if open_after: 
            open_file(download_folder + "/"+ file_name)

def open_file(path):
    print("🧾 Opening after download...")
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            os.system(f'open "{path}"')
        else:
            os.system(f'xdg-open "{path}"')
    except Exception:
        print("❌{RED} Could not open the file:{RESET} Try opening it manually with a PDF viewer.")

def program_exit():
    print(f"{YELLOW}Exiting program...{RESET}")
    raise SystemExit(0)