from concurrent.futures import ThreadPoolExecutor
import threading
from database import DBCMD, StructContextual

class Catalog:
    def __init__(self, database, auto=False):
        self.database = database
        # TODO: Implement by checking file system for new files in data directory
        self.auto = auto
        self.database_lock = threading.Lock()

    # Makes a struct from parameters and adds it to the database
    def create_struct(self, substructs, values, base_struct, position):
        with self.database_lock:
            id = self.database.query(DBCMD.GET_NEW_ID, False)
            struct = StructContextual(
                id,
                substructs,
                values,
                base_struct,
                position=position
            )
            self.database.query(DBCMD.ADD_STRUCT, struct)
            return struct

    def eval_database(self, size):
        max = size
        num_structs = len(self.database.query(DBCMD.GET_STRUCTS_BY_LENGTH, size))
        while num_structs == 2 ** (8*max):
            print("Max size fully discovered in database: ", max)
            max *= 2
            num_structs = len(self.database.query(DBCMD.GET_STRUCTS_BY_LENGTH, max))
            if num_structs != 2 ** (8*max):
                max = max // 2
        
        return max

    # Iteratively creates structs of a given size by pairing smaller structs
    # Used to find all possible structs of a given size
    def excavate_structs(self, size):
        existing = self.database.query(DBCMD.GET_STRUCTS_BY_LENGTH, size)
        substructs = self.database.query(DBCMD.GET_STRUCTS_BY_LENGTH, size // 2)
        
        def worker(first, second):
            skip = False
            for struct in existing:
                if (struct.substructs[0].id == first.id and
                    struct.substructs[1].id == second.id):
                    # Skip
                    skip = True
                    break
            if skip:
                return None
            # Otherwise, add it to the database
            return self.create_struct(
                [first, second],
                None,
                None,
                0
            )
        
        with ThreadPoolExecutor() as executor:
            # Submit tasks to the executor and collect the results
            futures = [executor.submit(worker, first, second) for first in substructs for second in substructs]
            # Wait for all tasks to complete and collect the results
            new_structs = [future.result() for future in futures if future.result() is not None]

            # Add new structs to the existing list
            existing.extend(new_structs)
                

    # Interprets byte data, saves important features to the database, and returns a blueprint of the data
    def try_catalog(self, data, chunk_size=1024):
        # TODO: Support uneven number of bytes
        if len(data) % 2 == 1:
            return []
        
        if len(self.database.query(DBCMD.GET_STRUCTS)) == 0:
            structs = self.init_structs(data)
        
        # Find max sized struct we have fully discovered
        byte_size = self.eval_database(1)
            
        # while byte_size < 2:
        #     self.excavate_structs(byte_size * 2)
        #     self.database.query(DBCMD.SAVE_DB)
        #     # Update evaluation
        #     byte_size = self.eval_database(byte_size)
        
        data_existing = self.database.query(DBCMD.GET_STRUCT_BY_DATA, data)
        
        if data_existing:
            return data_existing.to_blueprint()
        
        structs = []
        # Assuming database is populated, we use it for compression, prior to compression analysis 
        if len(self.database.query(DBCMD.GET_STRUCTS)) > 0:
            structs = self.database_compression(data, byte_size)
            if len(structs) == 0:
                structs = data
        
        final_struct = self.analyze_structs(structs)
        
        self.database.query(DBCMD.SAVE_DB)
        
        # Return array of bytes representing a blueprint
        return final_struct.to_blueprint()
    
    def database_compression(self, data, compression_ratio):
        compressed_structs = []
        
        # Initial compression, mainly to convert from array of bytes to array of structs
        existing_structs = self.database.query(DBCMD.GET_STRUCTS_BY_LENGTH, compression_ratio)
        segmented_data = self._segment_data(data, compression_ratio)
        
        def worker(segment):
            for struct in existing_structs:
                values = struct.get_values()
                if segment == values:
                    return struct
            return None

        with ThreadPoolExecutor() as executor:
            # Submit tasks to the executor and collect the results
            futures = [executor.submit(worker, segment) for segment in segmented_data]
            # Wait for all tasks to complete and collect the results
            results = [future.result() for future in futures]

        # Filter out None results and add to compressed_structs
        compressed_structs.extend(result for result in results if result is not None)
            
        return compressed_structs
    
    # Initialize byte structures before analysis
    def init_structs(self, data):
        # Data variable is an array of byte, ex: [0, 1, 150, 255, ...]
        struct_contextuals = []
        
        for i in range(256):
            self.database.query(DBCMD.ADD_STRUCT, StructContextual(i, values=[i]))
        for i, byte in enumerate(data):
            struct = self.database.query(DBCMD.GET_STRUCT_BY_ID, byte)
            struct.position = i
            struct_contextuals.append(struct)
        
        return struct_contextuals
    
    # Multi-pass relational analysis of the bit structs
    # Returns a single struct with equal values to the given structs
    def analyze_structs(self, structs):
        # TODO: Curate compression to get more meaningful abstractions? File-type specific stuff?
        # Compresses structs
        return self.factor_compression(structs, -1)[0]
    
    # Iteratively replaces groups of structs with a single struct
    # Compression rate is (2 ^ factor)
    def factor_compression(self, structs, factor=2):
        if factor == 0:
            return structs
        if factor < 0:
            factor = 1
            max_bits = len(structs)
            # Gets maximum number of times we can compress
            while (2 ** factor) < max_bits:
                factor += 1
        
        last_structs = structs.copy()
        for i in range(factor):
            last_structs = self.compress_structs(last_structs)
        
        return last_structs
    
    # Groups structs by 2 and replaces those groups with a single struct
    def compress_structs(self, structs):
        uniques = self.find_uniques_grouped(structs, 2)
        unique_structs = self.structs_from_structs(uniques)
        
        new_structs = []
        struct_groups = self._group_structs(structs, 2)
        for group in struct_groups:
            values = self.values_from_group(group)
            for struct in unique_structs:
                if struct.get_values() == values:
                    struct.position = len(new_structs)
                    new_structs.append(struct)
                    break
        if len(new_structs) == 0:
            return structs
        
        return new_structs
    
    # Scans structs for duplicate groups of a given size and assigns them to classes
    def find_uniques_grouped(self, structs, size):
        classes = []
        group_structs = self._group_structs(structs, size)
        
        def worker(group):
            if len(classes) >  0:
                exists = False
                for class_groups in classes:
                    class_group_vals = []
                    for struct in class_groups[0]:
                        class_group_vals.extend(struct.get_values())
                    group_vals = []
                    for struct in group:
                        group_vals.extend(struct.get_values())
                    
                    if class_group_vals == group_vals:
                        exists = True
                        break
                if exists:
                    return None
            return group

        with ThreadPoolExecutor() as executor:
            # Submit tasks to the executor and collect the results
            futures = [executor.submit(worker, group) for group in group_structs]
            # Wait for all tasks to complete and collect the results
            results = [future.result() for future in futures if future.result() is not None]

        for result in results:
            classes.append([result])

        return classes
    
    def structs_from_structs(self, structs):
        def worker(group):
            i, group = group
            substructs = group[0]
            struct_existing = self.database.query(DBCMD.GET_STRUCT_BY_SUBSTRUCTS, substructs, False)
            if struct_existing:
                struct_existing.position = i
                return struct_existing
            else:
                return self.create_struct(
                    substructs,
                    None,
                    substructs[0].base_struct,
                    position=i
                )

        with ThreadPoolExecutor() as executor:
            # Prepare the data for the executor
            data_for_executor = [(i, group) for i, group in enumerate(structs)]
            # Submit tasks to the executor and collect the results
            futures = [executor.submit(worker, group) for group in data_for_executor]
            # Wait for all tasks to complete and collect the results
            new_structs = [future.result() for future in futures]

        # TODO Figure out if we can use relations to be make this more efficient
        #for struct in new_structs:
        #    struct.update_context(new_structs)
        # Separate because it requires general relations to be finished first
        #for struct in new_structs:
        #    struct.update_specific_relations()

        return new_structs
    
    # Groups structs together by a given size
    def _group_structs(self, structs, size):
        groups = []
        for i in range(0, len(structs), size):
            group = structs[i:i+size]
            groups.append(group)
        return groups
    
    def values_from_group(self, group):
        values = []
        for struct in group:
            values.extend(struct.get_values())
        
        return values
    
    def _segment_data(self, data, num_bits):
        # Split binary data into chunks of specified size
        chunks = []
        for i in range(0, len(data), num_bits):
            chunk = []
            
            if num_bits == 1:
                chunk = [data[i]]
            else:
                chunk = data[i:i+num_bits]
            
            chunks.append(chunk)

        return chunks