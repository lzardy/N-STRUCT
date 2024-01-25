import os
from error_handler import handle_errors
from file_io import write

@handle_errors
class Settings:
    def __init__(self, file="settings.ini"):
        _, ext = os.path.splitext(file)
        if ext.lower() != ".ini":
            raise ValueError("Invalid settings file given")
        self.data_directory = "/data"
        self.auto_catalogue = True
        
        default_settings = f"{self.data_directory}\n{str(int(self.auto_catalogue))}"
        if not os.path.exists(file):
            write(file, default_settings)
        self._load_settings(file)

    # TODO: Make this cleaner
    def _load_settings(self, file):
        with open(file, 'r') as f:
            for i in range(len(f)):
                line = f[i]
                if line.strip() and not line.startswith('#'):
                    line = line.strip()
                    if i == 0:
                        if os.path.exists(line):
                            self.data_directory = line
                        else:
                            raise ValueError("Invalid data directory")
                    if i == 1:
                        if int(line) != 1:
                            self.auto_catalogue = False