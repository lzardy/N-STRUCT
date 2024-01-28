from file_io import read_bytes, write_bytes
import os
import sys
from settings import Settings
from catalog import Catalog
from database import Database

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
            file_path = os.path.join(os.getcwd(), sys.argv[1])
        else:
            raise ValueError("No file path provided")
        
        self.settings = Settings()
       
        data_dir = os.path.join(os.getcwd(), self.settings.data_directory)
        self.database = Database(data_dir)
       
        self.catalog = Catalog(self.database, self.settings.auto_catalog)
        
        file_data = read_bytes(file_path)
        print(file_data)
        blueprint = self.catalog.try_catalog(file_data)

        # Save blueprint to file
        print("saving blueprint: ", os.path.join(data_dir, "blueprint.json"))
        write_bytes(os.path.join(data_dir, "blueprint.json"), blueprint.data)

if __name__ == "__main__":
    Manager()