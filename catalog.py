import math
from database import StructBase, StructPrimitive, DBCMD, STYPE
from serializer import to_file

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
    
    # Update context and general struct relations
    def update_context(self, context):
        self.set_context(context)
        self.update_general_relations()
    
    def to_blueprint(self, full=False):
        data = []
        data.append("SBP")
        data.extend(self.get_substructs(full))
        
        return to_file(data)
         

# The relationships a struct has with other structs
class StructRelations:
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

    # Makes a struct from parameters and adds it to the database
    def create_struct(self, substructs, values, base_struct, position):
        id = self.database.query(DBCMD.GET_NEW_ID)
        struct = StructContextual(
            id,
            substructs,
            values,
            base_struct,
            position=position
        )
        self.database.query(DBCMD.SET_STRUCT, id, struct)
        return struct

    # Interprets bit data, saves important features to the database, and returns a blueprint of the data
    def try_catalog(self, data, chunk_size=1024):
        # Segment for efficiency
        data_chunks = self._segment_data(data, chunk_size)
        
        data_structs = []
        for chunk in data_chunks:
            # Try replacing data with existing struct in database
            struct_existing = self.database.struct_db.get_struct(data)
            if struct_existing:
                data_structs.append(struct_existing)
                continue
            
            structs = self.init_structs(chunk)
            # Gets a single struct to represent all of the data
            data_struct = self.find_relations(structs)[0]
            data_structs.append(data_struct)
        # Return array of bytes representing a blueprint
        return self.find_relations(data_structs)[0].to_blueprint()
    
    # Initialize bit structures before finding relations
    def init_structs(self, data):
        return self.structs_from_data(data)
    
    def structs_from_data(self, data):
        # Data variable is an array of bits, ex: [0, 1, 1, 0, ...]
        bit_struct = self.database.struct_db.structs[0]
        struct_contextuals = []
        
        # Replace all bits with contextual bit structs
        for i, bit in enumerate(data):
            struct = StructContextual(0, values=[bit], base_struct=bit_struct, position=i, context=struct_contextuals)
            struct_contextuals.append(struct)
            
        # Update relations
        for struct in struct_contextuals:
            struct.update_context(struct_contextuals)
        # Separate because it requires general relations to be finished first
        for struct in struct_contextuals:
            struct.update_specific_relations()
        
        return struct_contextuals
    
    def structs_from_structs(self, structs):
        new_structs = []
        for i, group in enumerate(structs):
            new_structs.append(self.create_struct(
                group[0],
                self.values_from_group(group[0]),
                group[0][0].base_struct,
                position=i
            ))
        
        # Update relations
        for struct in new_structs:
            struct.update_context(new_structs)
        # Separate because it requires general relations to be finished first
        for struct in new_structs:
            struct.update_specific_relations()
        
        return new_structs
    
    def values_from_group(self, group):
        values = []
        for struct in group:
            for value in struct.values:
                values.append(value)
        
        return values
    
    # Compresses structs by replacing groups of structs with a single struct
    # Compression rate is (2 ^ factor)
    def compress_structs(self, structs, factor=2):
        if factor == 0:
            return structs
        if factor < 0:
            factor = 0
            max_bits = len(structs)
            # Sets factor to largest exponent which does not exceed structs length
            while (2 ** factor) < max_bits:
                value = 2 ** factor
                if value < max_bits:
                    factor += 1
        
        last_structs = structs.copy()
        for i in range(factor):
            uniques = self.find_uniques_all(last_structs, 2)
            unique_structs = self.structs_from_structs(uniques)
            
            new_structs = []
            struct_groups = self._group_structs(last_structs, 2)
            for group in struct_groups:
                values = self.values_from_group(group)
                for struct in unique_structs:
                    if struct.values == values:
                        new_structs.append(struct)
                        break
            last_structs = new_structs
        
        return last_structs
    
    # Multi-pass relational analysis of the bit structs
    # By default, the return value represents all structs as a single struct
    def find_relations(self, structs, factor=-1):
        # TODO: Curate compression to get more meaningful abstractions? File-type specific stuff?
        # Compresses structs
        compressed_structs = self.compress_structs(structs, factor)
        
        return compressed_structs
    
    # Scans structs for duplicate groups of a given size and assigns them to classes
    # Optionally searches for novel combinations with excavate parameter
    def find_uniques_all(self, structs, size, excavate=False, save_dupes=False):
        classes = []
        offset = 0
        
        if (excavate):
            while (offset < len(structs)):
                classes.append(self.find_uniques_grouped(structs, size, offset, save_dupes))
                offset += math.ceil(size / 2)
        else:
            classes = self.find_uniques_grouped(structs, size, save_dupes=save_dupes)
            
        return classes
    
    def find_uniques_grouped(self, structs, size, offset=0, save_dupes=False):
        classes = []
        group_structs = self._group_structs(structs[offset:], size)
        for group in group_structs:
            if len(classes) > 0:
                exists = False
                for class_groups in classes:
                    if class_groups[0] == group:
                        if save_dupes:
                            class_groups.append(group)
                        exists = True
                        break
                if exists:
                    continue
            classes.append([group])
        return classes

    # Scans structs for duplicates and assigns them to classes
    def find_uniques(self, structs):
        classes = []
        for struct in structs:
            if len(classes) > 0:
                exists = False
                for group in classes:
                    if group[0] == struct:
                        group.append(struct)
                        exists = True
                        break
                if exists:
                    continue
            classes.append([struct])
        return classes
    
    # Groups structs together by a given size
    def _group_structs(self, structs, size):
        groups = []
        for i in range(0, len(structs), size):
            group = structs[i:i+size]
            groups.append(group)
        return groups
    
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