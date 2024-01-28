from database import StructBase, StructData

class Catalog:
    def __init__(self, database, auto=False):
        self.database = database
        self.auto = auto

    def try_catalog(self, data):
        new_struct = StructData()
        if len(data) == 0:
            # Empty StructBase, id = None
            return new_struct
        
        return new_struct
    
    def get_struct_id(self, data):
        return

    def replace_with_tree(self, data):
        return

    def save_unseen_content(self, data):
        return