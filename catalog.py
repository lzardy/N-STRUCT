from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import islice
import threading
import time
from database import DBCMD, StructContextual

class Catalog:
    def __init__(self, database, auto=False):
        self.database = database
        # TODO: Implement by checking file system for new files in data directory
        self.auto = auto
        self.struct_cache = {}

    def try_catalog(self, data, chunk_size=1024):
        """
        Interprets bit data, saves important features to the database, and returns the bits for a blueprint of the data.

        Args:
            data (bits): The bit data to be interpreted.
            chunk_size (int, optional): The size of the chunks to be processed. Defaults to 1024.

        Returns:
            bits: An array of bits representing a blueprint of the data.

        Raises:
            None

        Notes:
            - If the database is empty, the function initializes the structs using the provided data.
            - The function determines if the data exists fully in the database. If it does, the function returns the blueprint of the existing struct.
            - The function evaluates the database and determines the maximum struct size.
            - If the maximum struct size is greater than 1, the function replaces the data with structs that most closely relate to the data.
                - The function sorts the structs by their positions in an array and returns the related structs.
                - The function analyzes the structs and returns the final struct.
            - The function saves the database and returns the bits of the final struct which will be the blueprint of the data.
        """
        if len(self.database.query(DBCMD.GET_STRUCTS)) == 0:
            structs = self.init_structs(data)
        
        # convert data to known substructs
        start_time = time.time()
        substructs = self.convert_to_substructs(data)
        print("Conversion time:", time.time() - start_time)
        # compress all substructs into one struct
        start_time = time.time()
        self.struct_cache = {}
        struct = self.struct_from_substructs(substructs)
        print("Reconstruction time: ", time.time() - start_time)
        # add & save to database
        struct = self.database.query(DBCMD.ADD_STRUCT, struct)
        self.database.query(DBCMD.SAVE_DB)
        
        # Return array of bytes representing a blueprint of the data
        return struct.to_blueprint()
    
    # Creates structs from groups of substructs of specified size
    def group_substructs(self, substructs, group_size):
        # Slightly faster than simple slicing
        def grouper(iterable, n):
            it = iter(iterable)
            while True:
                chunk = list(islice(it, n))
                if not chunk:
                    break
                yield chunk

        new_structs = []
        for group in grouper(substructs, group_size):
            struct = StructContextual(substructs=group)
            struct = self.database.query(DBCMD.ADD_STRUCT, struct)
            new_structs.append(struct)
        
        return new_structs
    
    # Recursively creates new structs from pairs of integers (struct ids)
    # Returns a single struct with two substructs to represent the parent in the tree of substructs
    def struct_from_substructs(self, substructs):
        if len(substructs) == 1:
            return substructs[0]
        
        while len(substructs) > 1:
            print("substructs len:", len(substructs))
            
            last_substruct = None
            if len(substructs) % 2 != 0:
                last_substruct = substructs.pop()
            
            substructs = self.group_substructs(substructs, 2)
            
            if last_substruct:
                substructs.append(last_substruct)
                
        return substructs[0]
    
    # Makes a struct from parameters and adds it to the database
    def create_struct(self, substructs):
        struct = StructContextual(substructs=substructs)
        return self.database.query(DBCMD.ADD_STRUCT, struct)
    
    # Initialize byte (0-255) structures before analysis
    def init_structs(self, data):
        # Data variable is an array of bits, ex: [0, 1, 1, 1, 0, 0, ...]
        struct_contextuals = []
        
        for i in range(256):
            if i == 0:
                struct = StructContextual(values=[0])
                struct = self.database.query(DBCMD.ADD_STRUCT, struct)
                struct_contextuals.append(struct)
                continue
            if i == 1:
                struct = StructContextual(values=[1])
                struct = self.database.query(DBCMD.ADD_STRUCT, struct)
                struct_contextuals.append(struct)
                continue
            
            # Convert i to an array of bits
            bits = [int(x) for x in bin(i)[2:]]
            print("init struct bits: ", bits)
            
            # Add struct
            substructs = self.convert_to_substructs(bits)
            struct = StructContextual(substructs=substructs)
            struct = self.database.query(DBCMD.ADD_STRUCT, struct)
            struct_contextuals.append(struct)
        
        return struct_contextuals
    
    # Converts raw bit data into substructs using a binary search
    def convert_to_substructs(self, data):
        substruct_ids = data.copy()
        check_structs = self.database.query(DBCMD.GET_STRUCTS)[255::-1]

        # Sort the structs based on their values
        #check_structs.sort(key=lambda x: x.get_values())

        for struct in check_structs:
            # Skip structs larger than the input data
            if len(struct.get_values()) > len(data):
                continue
            else:
                substruct_ids = self.struct_overlap(struct, substruct_ids)
            
            if len(substruct_ids) <= 2:
                break

        # Get structs from ids
        return self.structs_by_ids(substruct_ids)
    
    # Finds all overlaps between a given struct's values and the given bit data and replaces the bit data with the struct's id
    def struct_overlap(self, struct, data):
        cache_key = (struct.id, tuple(data))
        if cache_key in self.struct_cache:
            return self.struct_cache[cache_key]
        result = self._struct_overlap(struct,data)
        self.struct_cache[cache_key] = result
        return result
    
    def _struct_overlap(self, struct, data):
        values = struct.get_values()
        length = len(values)
        new_data = []
        i = 0
        while i < len(data):
            # Must match length, first value, and then all values
            if (i <= len(data) - length
                and data[i] == values[0]
                and data[i:i+length] == values):
                new_data.append(struct.id)
                i += length
            # Slide forward if no match
            else:
                new_data.append(data[i])
                i += 1
        return new_data
    
    # Gets all structs in the database which match the provided ids
    def structs_by_ids(self, ids):
        structs = []
        for id in ids:
            structs.append(self.database.query(DBCMD.GET_STRUCT_BY_ID, id))
        return structs

    # Gets the struct which matches the given data
    def struct_by_data(self, structs, data):
        for struct in structs:
            struct_values = []
            if struct.values:
                struct_values = struct.values
            else:
                struct_values = struct.get_values()
            if struct and struct_values == data:
                return struct.copy()
        return None
    
    # Splits a given data array into chunks of specified size
    def _segment_data(self, data, num_vals):
        chunks = []
        for i in range(0, len(data), num_vals):
            chunk = []
            
            if num_vals == 1:
                chunk = [data[i]]
            else:
                chunk = data[i:i+num_vals]
            
            chunks.append(chunk)

        return chunks