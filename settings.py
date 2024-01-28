import os
from error_handler import handle_errors
from file_io import write

class Settings:
    def __init__(self, file="settings.ini"):
        _, ext = os.path.splitext(file)
        if ext.lower() != ".ini":
            raise ValueError("Invalid settings file given")
        self.data_directory = "data"
        self.auto_catalog = False
        
        default_settings = f"{self.data_directory}\n{str(int(self.auto_catalog))}"
        
        settings_path = os.path.join(os.getcwd(), file)
        if not os.path.exists(settings_path):
            write(settings_path, default_settings)
        self._load_settings(settings_path)

    # TODO: Make this cleaner
    @handle_errors
    def _load_settings(self, file):
        with open(file, 'r') as f:
            lines = f.readlines()
            for i in range(len(lines)):
                line = lines[i].strip()
                if line and not line.startswith('#'):
                    if i == 0:
                        check_path = os.path.join(os.getcwd(), line)
                        if os.path.exists(line):
                            self.data_directory = line
                        else:
                            raise ValueError("Invalid data directory")
                    if i == 1:
                        if int(line) != 1:
                            self.auto_catalog = False