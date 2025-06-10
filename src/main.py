from easypapershell import *
from configuration import Configuration
import sys

def main() -> None:
    """
    Entry point for the Easy Past Papers CLI application.

    Sets up the environment, loads configuration, and starts the command loop.
    Handles keyboard interrupts and ensures incomplete downloads are cleaned up.
    """
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

if __name__ == '__main__':
    try:
        import readline
    except ImportError:
        import pyreadline3 as readline
    main()