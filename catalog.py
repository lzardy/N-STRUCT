from unittest.util import strclass
from database import StructBase, StructPrimitive, DBCMD, STYPE

# The current objective is to implement StructRelations by constructing a map of relationships in the data. Each data point (bit/byte/segment/etc) has a relationship with every other data point in an entire dataset.

# A struct with relations to other structures (in context)
class StructContextual(StructPrimitive):
    def __init__(self, id=None, substructs=None, data=None, base_struct=None, max_size=1, num_values=1, position=0, context=None, struct_type=STYPE.CONTEXTUAL):
        super().__init__(id, substructs, data, base_struct, max_size, num_values, struct_type)
        self.position = position # Index of this struct in context
        self.context = context or [] # List of StructContextuals ordered by appearance in data
        self.relations = StructRelations(self)

    def add_relation(self, other_struct, relation):
        self.relations[other_struct] = relation

    def remove_relation(self, other_struct):
        if other_struct in self.relations:
            del self.relations[other_struct]

    def get_relationship(self, other_struct):
        return self.relations.get(other_struct, None)
    
    def update_context(self, context):
        self.context = context

# The relationships a struct has with other structs
class StructRelations:
    def __init__(self, parent_struct):
        self.struct = parent_struct
        self.count = 0 # How frequently the parent struct's ID appears in context
        self.distances = {} # Where the parent struct is, relative to other structs
        self.count_diff = {} # Difference in how often the parent struct ID appears compared to other struct IDs

    # Finds how this data point relates to other data points in context
    def update_relations(self, context):
        set_pos = True
        for i, struct in enumerate(context):
            # Incrementing count
            if struct.id == self.struct.id:
                self.count += 1
            
            # Getting distance between other structs
            struct_pos = struct.relations.position
            self.distances[struct_pos] = abs(struct_pos - self.position)
        
        for struct in context:
            # Getting difference in struct counts
            struct_count = struct.relations.count
            self.count_diff[struct.id] = struct_count - self.count

class Catalog:
    def __init__(self, database, auto=False):
        self.database = database
        # TODO: Implement by checking file system for new files in data directory
        self.auto = auto

    def try_catalog(self, data):
        blueprint = StructBase(struct_type=STYPE.BLUEPRINT)
        
        self.first_pass(data)
        
        self.find_relations(data)
        
        # Return array of bits representing a blueprint
        return []
    
    # Multi-pass relational analysis of the bit data
    def find_relations(self, data):
        # TODO: Implement StructRelations
        pass
    
    def first_pass(self, data):
        bit_struct = self.database.structs[0]
        # Data variable is an array of bits, ex: [0, 0, 1, 1, 1, 0, 1, ...]
        struct_contextuals = []
        # Replace all bits with contextual bit structs
        for i, bit in enumerate(data):
            struct = StructContextual(0, base_struct=bit_struct, position=i, context=struct_contextuals)
            struct_contextuals.append(struct)
    
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