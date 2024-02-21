from enum import Enum, IntFlag
import os
from re import S
from error_handler import handle_errors
from file_io import read_bytes, write_bytes
from serializer import to_bytes

# TODO: Utilize ZStandard Compression

# Struct types
class STYPE(Enum):
    BASE = 0
    DATA = 1
    PRIMITIVE = 2
    CONTEXTUAL = 3
    BLUEPRINT = 4

# TODO: Implement an approach for Lempel-Ziv-Welch Compression

# Details what other structs make up a struct
class StructBase:
    def __init__(self, id=None, substructs=None, struct_type=STYPE.BASE):
        self.id = id
        if substructs:
            self.substructs = substructs
        else:
            self.substructs = []
        self.type = struct_type
    
    # Checks if this struct is equal to a given variable
    def __eq__(self, other):
        return (isinstance(other, StructBase) and
                other.substructs == self.substructs)
    
    # Adds a substruct to this struct
    def add_substruct(self, substruct):
        self.substructs.append(substruct)
    
    # Returns a copy of this struct
    def copy(self):
        return StructBase(self.id, self.substructs.copy(), self.type)
    
    def get_substructs(self, full_tree=False, by_id=True):
        structs = []
        
        for substruct in self.substructs:
            if by_id:
                structs.append(substruct.id)
            else:
                structs.append(substruct)
            if full_tree and len(substruct.substructs) > 0:
                structs.extend(substruct.get_substructs(by_id))
        return structs
    
    def to_blueprint(self, full=False):
        data = []
        data.append("SBP")
        data.extend(self.get_substructs(full))
        
        return bytes(to_bytes(data))

# TODO: Represents a struct through a data operation between some number of structs
# class StructDelta:

# Details the raw byte data that represents a struct and its substructs
# Should only be kept in memory when actively being used
class StructData(StructBase):
    def __init__(self, id=None, substructs=None, values=None, struct_type=STYPE.DATA):
        super().__init__(id, substructs, struct_type)
        if values:
            self.values = values
        else:
            self.values = []
    
    # Returns the data that this struct represents
    def get_values(self):
        if self.values:
            return self.values
        
        values = []
        if len(self.substructs) > 0:
            for struct in self.substructs:
                values.extend(struct.get_values())
        return values
    
    # Returns a copy of this struct
    def copy(self):
        return StructData(
            self.id, 
            self.substructs.copy(), 
            self.values.copy(), 
            self.type)

# A unique struct built using other structs
# Ex: Byte structs are 8 bits
class StructPrimitive(StructData):
    def __init__(self, id=None, substructs=None, values=None, base_struct=None, max_size=1, struct_type=STYPE.PRIMITIVE):
        super().__init__(id, substructs, values, struct_type)
        self.base_struct = base_struct
        self.max_size = max_size
    
    # Returns a copy of this struct
    def copy(self):
        return StructPrimitive(
            self.id,
            self.substructs.copy(),
            self.values.copy(),
            self.base_struct,
            self.max_size,
            self.type)
    
    # Calculates the maximum size the data of this struct can be
    def get_total_size(self):
        if self.base_struct:
            return self.max_size * self.base_struct.get_total_size()
        return self.max_size
    
    def to_bytes(self, full=False):
        data = []
        data.append(self.id)
        substructs = self.get_substructs(full)
        data.append(len(substructs))
        data.extend(substructs)
        data.append(self.type.value)
        values = self.values
        data.append(len(values))
        data.extend(values)
        if self.base_struct:
            data.append(self.base_struct.id)
        else:
            data.append(self.id)
        data.append(self.max_size)
        
        return to_bytes(data)
        
# A struct with relations to other structures (in context)
class StructContextual(StructPrimitive):
    def __init__(self, id=None, substructs=None, values=None, base_struct=None, max_size=1, position=0, context=None, struct_type=STYPE.CONTEXTUAL):
        super().__init__(id, substructs, values, base_struct, max_size, struct_type)
        self.position = position # Index of this struct in context
        self.context = context or [] # List of StructContextuals ordered by appearance in data
        self.relations = StructRelations()
    
    # Checks if this struct is equal to a given variable
    def __eq__(self, other):
        return ((super().__eq__(other) and
                 isinstance(other, StructContextual)) or
            (self.values == other.values and
            self.base_struct == other.base_struct and
            self.relations == other.relations)
        )
    
    # Returns a copy of this struct
    def copy(self):
        return StructContextual(
            self.id,
            self.substructs.copy(),
            self.values.copy(),
            self.base_struct,
            self.max_size,
            struct_type=self.type)
    
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
        
    def from_bytes(bytes):
        id = int.from_bytes(bytes[:4])

        substructs = []
        # Each substruct is 4 bytes, separated by 4 zero bytes
        substruct_count = int.from_bytes(bytes[8:12])
        substructs_end = 16+(substruct_count*8)
        if substruct_count > 0:
            substructs_data = bytes[16:substructs_end]
            while substructs_data:
                substructs.append(int.from_bytes(substructs_data[:4]))
                substructs_data = substructs_data[8:]
        
        type = STYPE(int.from_bytes(bytes[substructs_end:substructs_end+4]))
        
        values = []
        value_count = int.from_bytes(bytes[substructs_end+8:substructs_end+12])
        values_end = substructs_end+16+(value_count*8)
        if value_count > 0:
            values_data = bytes[substructs_end+16:values_end]
            while values_data:
                values.append(int.from_bytes(values_data[:4]))
                values_data = values_data[8:]
        
        base_struct = int.from_bytes(bytes[values_end:values_end+4])
        max_size = int.from_bytes(bytes[values_end+8:values_end+12])
        
        # TODO: type and base_struct (if necessary)
        return StructContextual(id, substructs, values, max_size=max_size)

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

# Points to a StructData for quick access to StructData/StructBase locations in byte data
# Kept in memory while idle
class StructPointer:
    def __init__(self, id, index):
        self.structID = id
        self.byteIndex = index
        
    def from_bytes(bytes):
        return StructPointer(int.from_bytes(bytes[:4]), int.from_bytes(bytes[8:]))
        
    def to_bytes(self):
        data = []
        data.append(self.structID)
        data.append(self.byteIndex)
        return to_bytes(data)

# The Struct Database File containing all database information
class StructDatabase:
    def __init__(self, ptrs=None, structs=None):
        if ptrs and structs:
            self.ptrs = ptrs
            self.structs = structs
        else:
            # Contains StructPointers, allows for quick access to StructData/StructBase locations in data
            self.ptrs = []
            # Contains struct objects
            # TODO: Implement queuing when adding structs and a temporary struct cache for commonly used structs during runtime and cataloging
            self.structs = []
            
            #self.default_fill()
    
    # Fills structs array with default structures (bit, byte, integer, float, etc.)
    #def default_fill(self):
        # TODO: Verify if we want to generate all possible values for each struct
        # Bits (0 or 1)
        #bit = StructPrimitive(0, values=[0])
        #self.structs.append(bit)
        #self.structs.append(StructPrimitive(1, values=[1], base_struct=bit))
        # Bytes (0-255)
        #byte = StructPrimitive(1, base_struct=bit, max_size=8)
        #self.structs.append(byte)
        # Integers/Characters (0-2^32-1), ASCII is 1 byte, unicode is 1-4 bytes
        #numeric = StructPrimitive(2, base_struct=byte, max_size=4)
        #self.structs.append(numeric)
        # Floats (0-2^128-1), 8-bit floats are real I swear!
        #floating_point = StructPrimitive(3, base_struct=byte, max_size=16)
        #self.structs.append(floating_point)
        # Arrays are a dynamic container and are contextual
        # So, we leave them for the catalog to declare
    
    # Get the struct that has the given data
    def get_struct(self, values):
        for struct in self.structs:
            struct_values = []
            if struct.values:
                struct_values = struct.values
            else:
                struct_values = struct.get_values()
                
            if struct and struct_values == values:
                return struct.copy()
        return None
    
    # Get the struct that has the given substructs
    def get_substructs_owner(self, substructs, ids=False):
        substruct_ids = []
        
        if ids:
            substruct_ids = substructs
        else:
            for struct in substructs:
                substruct_ids.append(struct.id)
        
        for struct in self.structs:
            struct_ids = struct.get_substructs(False, True)
            # If all substruct IDs are matching
            if struct_ids == substruct_ids:
                return struct.copy()
        return None
    
    # Get the id of a struct by data
    def get_id(self, values):
        for struct in self.structs:
            if struct.values == values:
                return struct.id
        return None
    
    # Gets the data of a struct by ID
    def get_data(self, id):
        try:
            struct = self.structs[id]
            if struct.type == STYPE.DATA:
                return struct.values
            else:
                data = []
                for substruct in struct.substructs:
                    data.append(self.get_data(substruct))
                return data
        except:
            return []
    
    # Gets the data of a struct by struct
    def get_data(self, struct):
        if struct.type == STYPE.DATA:
            return struct.values
        else:
            data = []
            for substruct in struct.substructs:
                data.append(self.get_data(substruct))
            return data
    
    # Returns the byte data for the Database and Pointers files
    def to_sdb(self):
        # Database data
        db_data = []
        db_data.append("SDB")
        
        byte_data = to_bytes(db_data)
        next_byte = len(byte_data)
        ptrs = []
        for struct in self.structs:
            # Next byte will be the start of structs data
            ptrs.append(StructPointer(struct.id, next_byte))
            struct_data = struct.to_bytes()
            byte_data.extend(struct_data)
            next_byte += len(struct_data)
        
        ptr_data = []
        ptr_data.append("SDBP")
        ptr_file_data = to_bytes(ptr_data)
        for ptr in ptrs:
            ptr_file_data.extend(ptr.to_bytes())
        
        return bytes(byte_data), bytes(ptr_file_data)

    @handle_errors
    def from_bytes(db_bytes, ptrs_bytes):
        # Match "SDB" and "SDBP"
        db_str = db_bytes[:3].decode('utf-8')
        ptrs_str = ptrs_bytes[:4].decode('utf-8')
        if db_str == "SDB" and ptrs_str == "SDBP":
            ptrs = []
            # Skip header
            ptrs_data = ptrs_bytes[8:]
            while ptrs_data:
                # Each data point is separated by 4 zero bytes
                pointer = StructPointer.from_bytes(ptrs_data[:12])
                ptrs.append(pointer)
                ptrs_data = ptrs_data[16:]  # Move to the next StructPointer data
            
            structs = []
            for i, ptr in enumerate(ptrs):
                if i+1 >= len(ptrs):
                    struct_data = db_bytes[ptr.byteIndex:]
                else:
                    next_struct = ptrs[i+1].byteIndex
                    struct_data = db_bytes[ptr.byteIndex:next_struct-4]
                
                struct = StructContextual.from_bytes(struct_data)
                structs.append(struct)
            
            # Replace substruct IDs with struct references
            for struct in structs:
                substructs = []
                for substruct_id in struct.substructs:
                    substructs.append(structs[substruct_id])
                struct.substructs = substructs
            
            return StructDatabase(ptrs, structs)
        else:
            raise ValueError("Invalid Database or Pointer file.")

# Database commands
class DBCMD(IntFlag):
    # Getters
    GET_NEW_ID = 1 << 0
    GET_DATA = 1 << 1
    GET_STRUCT_DATA = 1 << 2
    GET_STRUCT_BY_ID = 1 << 3
    GET_STRUCT_BY_DATA = 1 << 4
    GET_STRUCT_BY_SUBSTRUCTS = 1 << 5
    GET_SUB_IDS = 1 << 6
    GET_STRUCTS = 1 << 7
    
    # Setters
    SET_DATA = 1 << 8
    SET_STRUCT = 1 << 9
    ADD_STRUCT = 1 << 10
    
    # Others
    SAVE_DB = 1 << 11

# Container and handler which gets and sets data in the Struct Database File
class Database():
    @handle_errors
    def __init__(self, path):
        self.working_dir = path
        # Struct Database file containing all the structures
        self.sdb_path = os.path.join(self.working_dir, 'database.sdb')
        # Pointers file containing location data for individual structures, relevant for looking up stuff from the database file (quickly).
        self.ptrs_path = os.path.join(self.working_dir, 'pointers.sdbp')
        
        # Init database
        if not os.path.exists(self.sdb_path):
            write_bytes(self.sdb_path)
        
        if not os.path.exists(self.ptrs_path):
            write_bytes(self.ptrs_path)
        
        db_bytes = read_bytes(self.sdb_path)
        if db_bytes:
            ptrs_bytes = read_bytes(self.ptrs_path)
            if ptrs_bytes:
                self.struct_db = StructDatabase.from_bytes(db_bytes, ptrs_bytes)
            else:
                raise ValueError("Failed to load pointers for database.")
        else:
            self.struct_db = StructDatabase()
        
    CMDARGS = {
        DBCMD.GET_NEW_ID: (0, []),
        DBCMD.GET_DATA: (1, [int]),
        DBCMD.GET_STRUCT_DATA: (1, [object]),
        DBCMD.GET_STRUCT_BY_ID:(1, [object]),
        DBCMD.GET_STRUCT_BY_DATA:(1, [object]),
        DBCMD.GET_STRUCT_BY_SUBSTRUCTS:(2, [object, bool]),
        DBCMD.GET_SUB_IDS: (1, [int]),
        DBCMD.GET_STRUCTS: (0, []),
        DBCMD.SET_DATA: (2, [int, object]),
        DBCMD.SET_STRUCT: (2, [int, object]),
        DBCMD.ADD_STRUCT: (1, [object]),
        DBCMD.SAVE_DB: (0, []),
    }

    # Gets and reserves the next ID for a new struct
    # Essentially appends a new struct to the end of the database file
    def __getNewID__(self):
        new_id = len(self.struct_db.structs)
        self.struct_db.structs.append(None)
        
        return new_id

    # Retrieve data by ID
    def __getData__(self, id):
        return self.struct_db.get_data(id)
    
    # Retrieve data by struct
    def __getStructData__(self, struct):
        return self.struct_db.get_data(struct)
    
    # Retrieve struct by ID
    def __getStructByID__(self, id):
        if id >= len(self.struct_db.structs):
            return None
        return self.struct_db.structs[id]
    
    # Retrieve struct by data
    def __getStructByData__(self, data):
        return self.struct_db.get_struct(data)
    
    # Retrieve struct by substructs
    def __getStructBySubstructs__(self, substructs, ids):
        return self.struct_db.get_substructs_owner(substructs, ids)

    # Retrieve substruct IDs in given struct
    def __getSubIDs__(self, id):
        return self.struct_db.structs[id].substructs
    
    # Assigns data to a given ID
    def __setData__(self, id, data):
        struct = self.struct_db.structs[id]
        if struct.type != STYPE.DATA:
            self.struct_db.structs[id] = StructData(id, struct.substructs, data)
    
    # Assigns a struct to a given ID
    def __setStruct__(self, id, struct):
        self.struct_db.structs[id] = struct
    
    # Adds a struct to the database
    def __addStruct__(self, struct):
        if not self.__getStructByID__(struct.id):
            self.struct_db.structs.append(struct)
    
    # Saves the Struct Database file
    def __saveDB__(self):
        database_file, ptrs_file = self.struct_db.to_sdb()
        write_bytes(self.sdb_path, database_file)
        print("Saved Database to file:", self.sdb_path)
        write_bytes(self.ptrs_path, ptrs_file)
        print("Saved Pointers to file:", self.ptrs_path)
        
    # Checks if command + arguments are valid
    def __checkCMD__(self, cmd, args):
        if cmd not in self.CMDARGS:
            raise ValueError('Invalid command')

        expected_arg_count, expected_types = self.CMDARGS[cmd]
        if len(args) != expected_arg_count:
            raise ValueError(f'Expected {expected_arg_count} arguments, got {len(args)}')

        for arg, expected_type in zip(args, expected_types):
            if not isinstance(arg, expected_type):
                raise TypeError(f'Argument {arg} does not match expected type {expected_type.__name__}')
    
    @handle_errors
    # Handles database commands
    def query(self, cmd, *args):
        self.__checkCMD__(cmd, args)
        
        if cmd == DBCMD.GET_NEW_ID:
            return self.__getNewID__()
        elif cmd == DBCMD.GET_DATA:
            return self.__getData__(args[0])
        elif cmd == DBCMD.GET_STRUCT_DATA:
            return self.__getStructData__(args[0])
        elif cmd == DBCMD.GET_STRUCT_BY_ID:
            return self.__getStructByID__(args[0])
        elif cmd == DBCMD.GET_STRUCT_BY_DATA:
            return self.__getStructByData__(args[0])
        elif cmd == DBCMD.GET_STRUCT_BY_SUBSTRUCTS:
            return self.__getStructBySubstructs__(args[0], args[1])
        elif cmd == DBCMD.GET_SUB_IDS:
            return self.__getSubIDs__(args[0])
        elif cmd == DBCMD.GET_STRUCTS:
            return self.struct_db.structs
        elif cmd == DBCMD.SET_DATA:
            return self.__setData__(args[0], args[1])
        elif cmd == DBCMD.SET_STRUCT:
            return self.__setStruct__(args[0], args[1])
        elif cmd == DBCMD.ADD_STRUCT:
            return self.__addStruct__(args[0])
        elif cmd == DBCMD.SAVE_DB:
            return self.__saveDB__()