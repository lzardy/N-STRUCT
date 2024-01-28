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
        
        new_struct.data = data
        
        return new_struct
    
    def get_struct_id(self, data):
        return

    def replace_with_tree(self, data):
        return

    def save_unseen_content(self, data):
        return
    
    def _segment_data(self, data, num_bits):
        # Convert data to binary
        binary_data = bin(int.from_bytes(data, 'big'))[2:]

        # Split binary data into chunks of specified size
        chunks = [binary_data[i:i+num_bits] for i in range(0, len(binary_data), num_bits)]

        return chunks