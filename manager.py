from file_io import read_bits, write_bytes
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
            # Relative to working directory
            file_path = sys.argv[1]
        else:
            raise ValueError("No file path provided")
        
        self.settings = Settings()
       
        data_dir = os.path.join(os.getcwd(), self.settings.data_directory)
        self.database = Database(data_dir)
       
        self.catalog = Catalog(self.database, self.settings.auto_catalog)
        
        file_data = read_bits(file_path)
        blueprint = self.catalog.try_catalog(file_data)
        
        if not blueprint:
            print("Failed to generate blueprint!")
            return
        
        self.database.query(DBCMD.SAVE_DB)
        
        # Save blueprint to file
        print("Saving blueprint to: ", os.path.join(data_dir, "blueprint.sbp"))
        write_bytes(os.path.join(data_dir, "blueprint.sbp"), blueprint)

if __name__ == "__main__":
    Manager()