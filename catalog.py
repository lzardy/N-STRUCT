from unittest.util import strclass
from database import StructBase, DBCMD, STYPE

class Catalog:
    def __init__(self, database, auto=False):
        self.database = database
        # TODO: Implement by checking file system for new files in data directory
        self.auto = auto

    def try_catalog(self, data):
        blueprint = StructBase(struct_type=STYPE.BLUEPRINT)
        
        # Check if data exists in database
        struct_id = self.database.query(DBCMD.GET_ID, data)
        if struct_id:
            # Data exists in database
            blueprint.add_substruct(struct_id)
        else:
            # TODO: Implement struct detection/data overlap checking
            return []
        
        return blueprint.substructs

    def _segment_data(self, data, num_bits):
        # Convert data to binary
        binary_data = bin(int.from_bytes(data, 'big'))[2:]

        # Split binary data into chunks of specified size
        chunks = [binary_data[i:i+num_bits] for i in range(0, len(binary_data), num_bits)]

        return chunks