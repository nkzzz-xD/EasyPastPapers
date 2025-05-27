from request_handler import *

import re
import cmd
import shlex
import os
import platform

#TODO Add a configuration.json file to read the base link and the extensions.

base_url = "https://papers.gceguide.cc"
download_folder_path = "../papers"

#Add config stuff
#TODO refresh the config if its been a while

#TODO SPecimen papers "/Specimen Papers" 
#TODO Also try papers that are in the root directory
#Download bulk using get, e.g. get 0620_s17

class EasyPaperShell(cmd.Cmd):
    intro = "Welcome to Easy Past Papers. Type help or ? to list commands."

    prompt = f"{CYAN}Enter a command> {RESET}"

    def do_get(self, arg):
        """Download a specific paper.\nUsage: get (paper code) [-o]\nExample: get 0452_w04_qp_3 -o
        -o flag (optional): open file after download"""
        args = shlex.split(arg)
        file_name = args[0] if args else None
        if not file_name:
            print("❌ Please specify a file to download.")
            return
        open_after = '-o' in args
        past_paper_regex = r"^(\d{4})_([mswy])(\d{2})_(qp|ms|er|gt|sf|in|i2|sm|sp|su|ci|ir)(?:_(\d{1,2}))?"
        pattern = re.compile(past_paper_regex, re.IGNORECASE)
        match = pattern.search(file_name)
        if not match:
            print(f"""❌ Invalid file '{file_name}' as parameter to get. Enter a valid file.\
            \nExpected format: {YELLOW}(4-digit subject code){RESET}_{YELLOW}(session code)(2 digit year code){RESET}_{YELLOW}(paper type){RESET}_{YELLOW}(paper identifier){RESET}\
            \nExample: 0606_s17_qp_22""")
            return
        subject_code, session, year, paper_type, paper_num = match.groups()
        subject_link = None
        subject_exam = None
        for key, value in subjects.items():
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
        
        print("Preparing for download...")
        os.makedirs(download_folder_path, exist_ok = True)
        #now to find the file with the regex
        link_for_year = base_url + "/" + link_extensions[subject_exam] + "/" + subjects[subject_exam][subject_code] + "/20" + year
        html_for_year = safe_get_html(link_for_year)
        #Get the page with papers for that year.
        links = html_for_year.find_all('a')
        for link in links:
            link_str = link.get('href')
            if (re.search(file_name, link_str)):
                file_name = link_str.strip("/")
                break
        print(file_name)
        print(f"📥 Downloading {file_name}...")
        pdf_response = safe_get_response(link_for_year + "/" + file_name)
        file_path = download_folder_path + "/" + file_name
        with open(file_path, 'wb') as f:
            f.write(pdf_response.content)
        print(f"{GREEN}Done!{RESET}")

        if open_after:
            print("🧾 Opening after download...")
            open_file(file_path)

    def default(self, line):
        print(f"❌ Unknown command: '{line}'. Type 'help' to see available commands.")

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

if __name__ == '__main__':
    try:
        print("Setting up...")
        html_page = safe_get_html(base_url)
        global link_extensions
        link_extensions = find_link_extensions(html_page)
        global subjects
        subjects = find_subjects(base_url, link_extensions)
        import sys
        # Move cursor up 1 line and clear the line
        sys.stdout.write('\x1b[1A')  # Move cursor up
        sys.stdout.write('\x1b[2K')  # Clear entire line
        sys.stdout.flush()
        EasyPaperShell().cmdloop()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Exiting program...")