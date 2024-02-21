import math
from database import DBCMD, StructContextual

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
        self.database.query(DBCMD.ADD_STRUCT, StructContextual(0, values=[0]))
        self.database.query(DBCMD.ADD_STRUCT, StructContextual(1, values=[1]))
        
        data_existing = self.database.query(DBCMD.GET_STRUCT_BY_DATA, data)
        
        if data_existing:
            return data_existing.to_blueprint()
        
        structs = self.init_structs(data)
        final_struct = self.find_relations(structs)[0]
        
        # Return array of bytes representing a blueprint
        final_struct_values = final_struct.get_values()
        is_equal = final_struct_values == data
        return final_struct.to_blueprint()
    
    # Initialize bit structures before finding relations
    def init_structs(self, data):
        # Data variable is an array of bits, ex: [0, 1, 1, 0, ...]
        struct_contextuals = []
        for i, bit in enumerate(data):
            struct = self.database.query(DBCMD.GET_STRUCT_BY_ID, bit)
            struct.position = i
            struct_contextuals.append(struct)
        
        return struct_contextuals
    
    def structs_from_structs(self, structs):
        new_structs = []
        for i, group in enumerate(structs):
            substructs = group[0]
            struct_existing = self.database.query(DBCMD.GET_STRUCT_BY_SUBSTRUCTS, substructs, False)
            if struct_existing:
                new_structs.append(struct_existing)
                continue
            else:
                new_structs.append(self.create_struct(
                    substructs,
                    None,
                    substructs[0].base_struct,
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
            values.extend(struct.get_values())
        
        return values
    
    # Compresses structs by replacing groups of structs with a single struct
    # Compression rate is (2 ^ factor)
    def compress_structs(self, structs, factor=2):
        if factor == 0:
            return structs
        if factor < 0:
            factor = 1
            max_bits = len(structs)
            # Sets factor to largest exponent which does not exceed structs length
            while (2 ** factor) < max_bits:
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
                    if struct.get_values() == values:
                        new_structs.append(struct)
                        break
            if len(new_structs) == 0:
                return last_structs
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
                    class_group_vals = []
                    for struct in class_groups[0]:
                        class_group_vals.extend(struct.get_values())
                    group_vals = []
                    for struct in group:
                        group_vals.extend(struct.get_values())
                    
                    if class_group_vals == group_vals:
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