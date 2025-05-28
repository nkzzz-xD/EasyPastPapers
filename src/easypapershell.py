from requesthandler import *
import re
import cmd
import shlex
import os
import platform
from collections import OrderedDict

class EasyPaperShell(cmd.Cmd):

    #TODO Predict pdf for speed in most cases

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
        open_after = '-o' in args
        past_paper_regex = r"^(\d{4})_([mswy])(\d{2})_(qp|ms|er|gt|sf|in|i2|sm|sp|su|ci|ir)(?:_(\d{1,2}))?"
        pattern = re.compile(past_paper_regex, re.IGNORECASE)
        match = pattern.search(file_name)
        if not match:
            print(f"""❌ Invalid file '{file_name}' as parameter to get. Enter a valid file.\
            \nExpected format: {YELLOW}(4-digit subject code){RESET}_{YELLOW}(session code)(2 digit year code){RESET}_{YELLOW}(paper type){RESET}_{YELLOW}(paper identifier){RESET}\
            \nExample: {YELLOW}0606{RESET}_{YELLOW}s17{RESET}_{YELLOW}qp{RESET}_{YELLOW}22{RESET}""")
            return
        subject_code, session, year, paper_type, paper_num = match.groups()
        subject_link = None
        subject_exam = None
        for key, value in self.config.subjects.items():
            if subject_code in value.keys():
                subject_link = value[subject_code]
                subject_exam = key
                break
            
        if not subject_link:
            print(f"❌ Unknown subject code '{subject_code}'")
            return 
        files_needing_paper_num = {'qp', 'ms', 'sf'} #TODO Complete this

        if paper_type.lower() in files_needing_paper_num and paper_num is None:
            print(paper_type.lower() + " must have paper number")
            return
        
        print("\rPreparing for download...")
        #now to find the file with the regex
        link_for_subject = self.config.base_url + "/" + self.config.exam_page_links[subject_exam] + "/" + self.config.subjects[subject_exam][subject_code]
        link_for_year = link_for_subject + "/20" + year

        cache_key = (subject_code, year)
        if cache_key in self.page_cache:
            html_for_year = self.page_cache.get(cache_key)
            self.page_cache.move_to_end(cache_key)
        else:
            html_for_year = safe_get_html(link_for_year, False)
            if not html_for_year:
                link_for_year = link_for_subject
                html_for_year = safe_get_html(link_for_year)

            # To add to the cache
            self.page_cache[cache_key] = html_for_year
            if len(self.page_cache) > self.max_cache_size:
                self.page_cache.popitem(last = False)
        #Get the page with papers for that year.
        links = html_for_year.find_all('a')
        for link in links:
            link_str = link.get('href')
            if (re.search(file_name, link_str)):
                file_name = link_str.strip("/")
                break
        content_response = download_with_progress(link_for_year + "/" + file_name, 
                                                  self.config.download_folder + "/" + self.config.subjects[subject_exam][subject_code] + "/20" + year,
                                                  file_name)
        if not content_response:
            return

        if open_after:
            print("🧾 Opening after download...")
            # open_file(file_path)

    def default(self, line):
        print(f"❌ Unknown command: '{line}'. Type 'help' to see available commands.")

    def do_exit(self, arg):
        program_exit()

def open_file(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            os.system(f"open {path}")
        else:
            os.system(f"xdg-open {path}")
    except Exception:
        print("❌ Could not open the file. Try opening it manually with a PDF viewer.")

def program_exit():
    print(f"{YELLOW}Exiting program...{RESET}")
    raise SystemExit(0)