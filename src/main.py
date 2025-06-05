from easypapershell import *
from configuration import Configuration
import sys
# Only try to import readline if safe
if sys.platform == "win32" and sys.version_info >= (3, 13):
    import types

    class FakeReadline:
        backend = "fake"

        def get_completer(self):
            return None

        def set_completer(self, completer):
            pass

        def parse_and_bind(self, string):
            pass

        def get_line_buffer(self):
            return ""

    sys.modules['readline'] = FakeReadline()
    print("⚠️  Tab completion disabled (Windows + Python 3.13).") #Because of readline changes in Python 3.13, we cannot use readline for tab completion on Windows.


#TODO Add commands to change config stuff.
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