import os
from settings import Settings
from catalogue import Catalogue
from database import Database

# Order of operations in production:
# 1. Manager checks for new data
# 2. Manager sends new data to Catalogue
# 3a. Catalogue processes the data into an array of StructDatas or StructBases, using the Database as a reference and knowledge base
# 3b. If the catalogue finds data that cannot be represented by a StructBase, it will query getNewID() from the database and assign that ID to a new StructData
# 3c. If the catalogue finds data that can be represented by a StructBase, and the structure of the substructs in this StructBase is unique, it will query getNewID() from the database and assign that ID to a new StructData
# 4a. Catalogue queries the database for each StructData and StructBase it has constructed
# 4b. 
# 4c. 

class Manager:
   def __init__(self):
       self.settings = Settings()
       
       data_dir = os.path.join(os.getcwd(), self.settings.data_directory)
       db_file_path = os.path.join(data_dir, self.settings.database_file)
       self.database = Database(data_dir, db_file_path)
       
       self.catalogue = Catalogue(self.database, self.settings.auto_catalogue)