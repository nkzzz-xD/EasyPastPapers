from easypapershell import *
from configuration import Configuration
import sys

#TODO refresh the config if its been a while
#TODO Download bulk using get, e.g. get 0620_s17
#TODO Add tab completion

if __name__ == '__main__':
    try:
        print("Setting up...")
        global config
        config = Configuration()
        config.load_config()

        # Move cursor up 1 line and clear the line
        sys.stdout.write('\x1b[1A')  # Move cursor up
        sys.stdout.write('\x1b[2K')  # Clear entire line
        sys.stdout.flush()
        EasyPaperShell(config).cmdloop()
    except KeyboardInterrupt:
        print("")
        program_exit()
    finally:
        delete_incomplete_download()