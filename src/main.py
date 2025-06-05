from easypapershell import *
from configuration import Configuration
import sys
try:
    import readline
except ImportError:
    import pyreadline3 as readline

if __name__ == '__main__':
    try:
        print("Setting up...")
        Configuration.load_config()

        # Move cursor up 1 line and clear the line
        sys.stdout.write('\x1b[1A')  # Move cursor up
        sys.stdout.write('\x1b[2K')  # Clear entire line
        sys.stdout.flush()
        EasyPaperShell().cmdloop()
    except KeyboardInterrupt:
        print("")
        program_exit()
    finally:
        delete_incomplete_download()