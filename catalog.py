from unittest.util import strclass
from database import StructBase, DBCMD, STYPE

# The relationship a struct has with other structs
class StructRelations:
    def __init__(self, appearance, frequency, relativity, context=None):
        self.appearance = appearance
        self.frequency = frequency
        self.relativity = relativity
        self.context = context or {}  # Optional contextual attributes

    def calculate_relation(self, data_point):
        # Find how this data point relates to a given data point, based on the parameters
        pass

    def update_relation(self, data_point, new_relation):
        # Update parameters based on a given data point
        pass

class Catalog:
    def __init__(self, database, auto=False):
        self.database = database
        # TODO: Implement by checking file system for new files in data directory
        self.auto = auto

    def try_catalog(self, data):
        blueprint = StructBase(struct_type=STYPE.BLUEPRINT)
        
        self.first_pass(data)
        
        self.find_relations(data)
        
        # Return array of bits
        return []
    
    # Multi-pass relational analysis of the bit data
    def find_relations(self, data):
        # TODO: Use StructRelations
        pass
    
    # Checks which data points match 1:1 with structures in the database
    def first_pass(self, data):
        # This will store the structures as we match data
        tmp_data = []
        # Iterate on structs
        for struct in self.database.struct_db.structs:
            # Segment the data by max size of the struct
            segments = self._segment_data(data, struct.get_total_size())
            # Iterate on the segments
            for seg in segments:
                pass
            
    
    def _segment_data(self, data, num_bits):
        # Split binary data into chunks of specified size
        chunks = []
        for i in range(0, len(data), num_bits):
            chunk = []
            
            if num_bits == 1:
                chunk = data[i]
            else:
                chunk = data[i:i+num_bits]
            
            chunks.append(chunk)

        return chunks