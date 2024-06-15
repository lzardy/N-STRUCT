from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent.futures
import threading
from database import DBCMD, StructContextual

class Catalog:
    def __init__(self, database, auto=False):
        self.database = database
        # TODO: Implement by checking file system for new files in data directory
        self.auto = auto
        self.database_lock = threading.Lock()

    def try_catalog(self, data, chunk_size=1024):
        """
        Interprets byte data, saves important features to the database, and returns the bytes for a blueprint of the data.

        Args:
            data (bytes): The byte data to be interpreted.
            chunk_size (int, optional): The size of the chunks to be processed. Defaults to 1024.

        Returns:
            bytes: An array of bytes representing a blueprint of the data.

        Raises:
            None

        Notes:
            - If the database is empty, the function initializes the structs using the provided data.
            - The function determines if the data exists fully in the database. If it does, the function returns the blueprint of the existing struct.
            - The function evaluates the database and determines the maximum struct size.
            - If the maximum struct size is greater than 1, the function replaces the data with structs that most closely relate to the data.
                - The function sorts the structs by their positions in an array and returns the related structs.
                - The function analyzes the structs and returns the final struct.
            - The function saves the database and returns the bytes of the final struct which will be the blueprint of the data.
        """
        if len(self.database.query(DBCMD.GET_STRUCTS)) == 0:
            structs = self.init_structs(data)
        
        # Determine if data exists fully in database
        struct_existing = self.database.query(DBCMD.GET_STRUCT_BY_DATA, data)
        
        if struct_existing:
            return struct_existing.to_blueprint()
        
        size_max = self.eval_database()
        print("Max struct size:", size_max)
        
        if size_max > 1:
            # Replaces the data with structs which most closely relate to the data
            structs_related = []
            structs_unordered = self.iterate_unrelated(data.copy(), 0, size_max)

            # Sort by position
            structs_unordered = sorted(structs_unordered, key=lambda x: x[1])
            structs_related.extend([struct for struct, _, _ in structs_unordered])
            structs = structs_related
            
            print("Found related structs:", len(structs_related))
        
        final_struct = self.analyze_structs(structs)
        
        self.database.query(DBCMD.SAVE_DB)
        
        # Return array of bytes representing a blueprint
        return final_struct.to_blueprint()
    
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
    
    # Finds the maximum sized struct present in the database
    def eval_database(self):
        max_size = 0
        for struct in self.database.query(DBCMD.GET_STRUCTS):
            values = len(struct.get_values())
            if values > max_size:
                max_size = values
        return max_size

    def iterate_unrelated(self, data, start_position, max_size=1):
        if len(data) == 0:
            return None

        unordered_structs = []
        current_position = start_position

        while len(data) > 0:
            struct_related, position, length = self.get_related(data, max_size)
            unordered_structs.append((struct_related, current_position + position, length))
            data = data[position + length:]
            current_position += position + length

        return unordered_structs
    
    # Finds a struct in the database which most closely relates to the given data
    def get_related(self, data, max_size=1):
        # Iteratively split the data in half until we find a struct which has data that relates
        struct_related = None
        data_segmented = data
        if max_size < len(data):
            new_length = max_size
        else:
            new_length = len(data)
        while not struct_related:
            known_structs = self.database.query(DBCMD.GET_STRUCTS_BY_LENGTH, new_length)
            if len(known_structs) == 0:
                new_length -= 1
                continue
            
            if new_length == 1:
                for byte in data:
                    struct_related = self.database.query(DBCMD.GET_STRUCT_BY_ID, byte)
                    if struct_related:
                        break
            
            data_segmented = self._segment_data(data, new_length)
            position = 0
            for segment in data_segmented:
                if len(segment) < new_length:
                    continue
                struct_related = self.struct_by_data(known_structs, segment)
                if struct_related:
                    break
                position += len(segment)
            if new_length > 1:
                new_length -= 1
            else:
                break
        
        return struct_related, position, new_length

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
            last_structs = self.compress_structs(last_structs, 2)
            if len(last_structs) == 1:
                break
            
        last_structs = structs.copy()
        for i in range(factor):
            last_structs = self.compress_structs(last_structs, 3)
            if len(last_structs) == 1:
                break
        
        last_structs = structs.copy()
        for i in range(factor):
            j = 2
            while j != 4:
                last_structs = self.compress_structs(last_structs, j)
                j += 1
                if len(last_structs) == 1:
                    break
            if len(last_structs) == 1:
                break
        
        return last_structs
    
    # Groups structs by 2 and replaces those groups with a single struct
    def compress_structs(self, structs, group_size=2):
        uniques = self.find_uniques_grouped(structs, group_size)
        unique_structs = self.structs_from_structs(uniques)
        
        new_structs = []
        struct_groups = self._group_structs(structs, group_size)
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
    
    # Groups structs together by a given size
    def _group_structs(self, structs, size):
        def worker(i):
            return structs[i:i+size]

        with ThreadPoolExecutor() as executor:
            # Submit tasks to the executor and collect the results
            futures = [executor.submit(worker, i) for i in range(0, len(structs), size)]
            # Wait for all tasks to complete and collect the results
            groups = [future.result() for future in futures]

        return groups
    
    def values_from_group(self, group):
        def worker(struct):
            return struct.get_values()

        with ThreadPoolExecutor() as executor:
            # Submit tasks to the executor and collect the results
            futures = [executor.submit(worker, struct) for struct in group]
            # Wait for all tasks to complete and collect the results
            values = [future.result() for future in futures]

        # Flatten the list of lists into a single list
        return [value for sublist in values for value in sublist]
    
    # Splits binary data into chunks of specified size
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