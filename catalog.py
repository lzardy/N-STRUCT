from unittest.util import strclass
from database import StructBase, StructPrimitive, DBCMD, STYPE

# The current objective is to implement StructRelations by constructing a map of relationships in the data. Each data point (bit/byte/segment/etc) has a relationship with every other data point in an entire dataset.

# A struct with relations to other structures (in context)
class StructContextual(StructPrimitive):
    def __init__(self, id=None, substructs=None, values=None, base_struct=None, max_size=1, num_values=1, position=0, context=None, struct_type=STYPE.CONTEXTUAL):
        super().__init__(id, substructs, values, base_struct, max_size, num_values, struct_type)
        self.position = position # Index of this struct in context
        self.context = context or [] # List of StructContextuals ordered by appearance in data
        self.relations = StructRelations()
    
    # Checks if this struct is equal to a given variable
    def __eq__(self, other):
        if not isinstance(other, StructContextual):
            return False
        return (
            self.values == other.values and
            self.base_struct == other.base_struct and
            self.relations == other.relations
        )
    
    def set_context(self, context):
        self.context = context
    
    # Updates count and distance
    def update_general_relations(self):
        for i, struct in enumerate(self.context):
            # Incrementing count
            if struct.values == self.values:
                self.relations.count += 1
            
            # Getting distance between other structs
            struct_pos = struct.position
            self.relations.distances[struct_pos] = abs(struct_pos - self.position)
    
    # Updates count_diff, specific relations use other struct relations
    def update_specific_relations(self):
        for struct in self.context:
            # Getting difference in struct counts
            struct_count = struct.relations.count
            self.relations.count_diff[struct.position] = struct_count - self.relations.count

# The relationships a struct has with other structs
class StructRelations:#
    def __init__(self):
        self.count = 0 # How frequently the parent struct's values appear in context
        self.distances = {} # Where the parent struct is, relative to other structs
        self.count_diff = {} # Difference in how often the parent struct's values appear compared to other structs
        
    # Checks if current relations are equal to the given relations
    def __eq__(self, other):
        if not isinstance(other, StructRelations):
            return False
        
        # Simple K-Nearest Neighbors for distance equivalence, k = 1 is good enough!
        k = 1
        distance_differences = [abs(self.distances[key] - other.distances[key]) for key in self.distances.keys() & other.distances.keys()]
        # Sort and select top k smallest differences
        sorted_differences = sorted(distance_differences)[:k]
        # Average of k smallest differences
        avg_difference = sum(sorted_differences) / k
        # Threshold for equality
        threshold =  1.0
        distance_equal = avg_difference <= threshold
        
        return (
            self.count == other.count and
            self.count_diff == other.count_diff and
            distance_equal
        )

class Catalog:
    def __init__(self, database, auto=False):
        self.database = database
        # TODO: Implement by checking file system for new files in data directory
        self.auto = auto

    def try_catalog(self, data):
        blueprint = StructBase(struct_type=STYPE.BLUEPRINT)
        
        structs = self.init_context(data)
        self.find_relations(structs)
        
        # Return array of bits representing a blueprint
        return []
    
    # Initialize bit structures before finding relations
    def init_context(self, data):
        bit_struct = self.database.struct_db.structs[0]
        # Data variable is an array of bits, ex: [0, 0, 1, 1, 1, 0, 1, ...]
        struct_contextuals = []
        
        # Replace all bits with contextual bit structs
        for i, bit in enumerate(data):
            struct = StructContextual(0, values=[bit], base_struct=bit_struct, position=i, context=struct_contextuals)
            struct_contextuals.append(struct)
            
        # Update context and general struct relations
        for struct in struct_contextuals:
            struct.set_context(struct_contextuals)
            struct.update_general_relations()
            
        return struct_contextuals
    
    # Multi-pass relational analysis of the bit structs
    def find_relations(self, structs):
        # Update all specific struct relations
        for struct in structs:
            struct.update_specific_relations()
            
            #print(f"Index: {struct.position}, Values: {struct.values}, Count: {struct.relations.count}, Count Differences: {struct.relations.count_diff}")
            
        # Iterative, variable-size group search
        #self.find_patterns(structs)
    
    # Scans structs by grouping and finds patterns between groups 
    def find_patterns(self, structs):
        classes = []
        size = 1
        while size <= len(structs):
            # Array of arrays containing bits
            groups = self._segment_data(structs, size)
            # TODO: Finish
            
    # Scans given contextual structures for duplicates and assigns them to classes
    def find_uniques(self, structs):
        classes = []
        for struct in structs:
            if len(classes) > 0:
                exists = False
                for struct_group in classes:
                    if struct_group[0] == struct:
                        struct_group.append(struct)
                        exists = True
                        break
                if exists:
                    continue
            
            classes.append([struct])
        
        return classes
    
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