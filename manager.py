import time
from error_handler import handle_errors
from file_io import read_bits, read_bytes, write_bits, write_bytes
import os
import sys
from settings import Settings
from catalog import Catalog
from database import DBCMD, Database

# Order of operations in production:
# 1. Manager checks for new data or user inputs a file
# 2. Manager sends new data to Catalog
# 3a. Catalog compares new data to existing data
# 3b. If new data exists 1 to 1 in the Database, it is replaced with a StructBase from the Database
# 3c. If new data does not exist 1 to 1 in the Database, each StructData in the Database is compared to the new data
# 3d. If new data contains a StructData from the Database, a new StructData is created with the new data and the existing StructData is added as a StructBase subtruct
# 3e. If new data does not contain a StructData from the Database, a new StructData is created with the new data

class Manager:
    def __init__(self):
        if len(sys.argv) > 1:
            self.settings = Settings()
            data_dir = os.path.join(os.getcwd(), self.settings.data_directory)
            self.database = Database(data_dir)
            self.catalog = Catalog(self.database, self.settings.auto_catalog)
            
            # Relative to working directory
            input_path = sys.argv[1]
            if os.path.isdir(input_path):
                folder_path = input_path
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        self.process_file(file_path, data_dir)
            elif os.path.isfile(input_path):
                self.process_file(input_path, data_dir)
                return
            else:
                raise ValueError("Provided path is neither a directory nor a file")
        else:
            raise ValueError("No input path provided")

    def process_file(self, file_path, data_dir):
        start_time = time.time()
        file_data = read_bytes(file_path)
        
        if not file_data:
            print(f"File not found or unreadable: {file_path}")
            return
        
        if self.is_blueprint(file_data):
            file_data = self.database.query(DBCMD.GET_BLUEPRINT_BYTES, file_data[7:])
            bp_raw_path = os.path.join(data_dir, "blueprint.raw")
            write_bits(bp_raw_path, file_data)
            print(f"Saved raw blueprint data to: {bp_raw_path}")
            return
        
        file_data = [byte for byte in file_data]
        blueprint = self.catalog.try_catalog(file_data)
        
        if not blueprint:
            print("Failed to generate blueprint!")
            return
        
        end_time = time.time() # Record the end time
        cataloging_duration = end_time - start_time # Calculate the duration
        
        print(f"Catalogued file {file_path} in: {int(cataloging_duration)} seconds.")
        
        # Save blueprint to file
        print(f"Saving blueprint to: {os.path.join(data_dir, 'blueprint.sbp')}")
        write_bytes(os.path.join(data_dir, "blueprint.sbp"), blueprint)

    def is_blueprint(self, bytes):
        # Match "SBP"
        try:
            sbp_str = bytes[:3].decode('utf-8')
            return sbp_str == "SBP"
        except:
            return False

if __name__ == "__main__":
    Manager()