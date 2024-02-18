from enum import Enum, IntFlag
import os
from re import S
from error_handler import handle_errors
from file_io import read_bits, write_bits, read_bytes, write_bytes

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

# TODO: Represents a struct through a data operation between some number of structs
# class StructDelta:

# Details the raw byte data that represents a struct and its substructs
# Should only be kept in memory when actively being used
class StructData(StructBase):
    def __init__(self, id=None, substructs=None, values=None, num_values=1, struct_type=STYPE.DATA):
        super().__init__(id, substructs, struct_type)
        if values:
            self.values = values
        else:
            self.values = []
        # Number of possible values this struct can represent (from 0)
        self.num_values = num_values
    
    # Returns a list of all possible values this struct can represent
    def get_values(self):
        values = []
        for value in range(self.num_values):
            values.append(value)
    
    # Returns a copy of this struct
    def copy(self):
        return StructData(self.id, self.substructs.copy(), self.values.copy(), self.num_values, self.type)

# A unique struct built using other structs
# Ex: Byte structs are 8 bits
class StructPrimitive(StructData):
    def __init__(self, id=None, substructs=None, values=None, base_struct=None, max_size=1, num_values=1, struct_type=STYPE.PRIMITIVE):
        super().__init__(id, substructs, values, num_values, struct_type)
        self.base_struct = base_struct
        self.max_size = max_size
    
    # Calculates the maximum size the data of this struct can be
    def get_total_size(self):
        if self.base_struct:
            return self.max_size * self.base_struct.get_total_size()
        return self.max_size
        
# Points to a StructData for quick access to StructData/StructBase locations in byte data
# Kept in memory while idle
class StructPointer:
    def __init__(self, id, index):
        self.structID = id
        self.byteIndex = index

# The Struct Database File containing all database information
class StructDatabase:
    def __init__(self, file_path):
        # Contains the raw database byte data
        self.data = read_bytes(file_path)
        # Contains StructPointers, allows for quick access to StructData/StructBase locations in data
        self.ptrs = []
        # Contains StructBases/StructCounts
        # TODO: Implement queuing when adding structs and a temporary struct cache for commonly used structs during runtime and cataloging
        self.structs = []
        
        self.default_fill()
    
    # Fills structs array with default structures (bit, byte, integer, float, etc.)
    def default_fill(self):
        # TODO: Verify if we want to generate all possible values for each struct
        # Bits (0 or 1)
        bit = StructPrimitive(0, num_values=2)
        self.structs.append(bit)
        # Bytes (0-255)
        byte = StructPrimitive(1, base_struct=bit, max_size=8)
        self.structs.append(byte)
        # Integers/Characters (0-2^32-1), ASCII is 1 byte, unicode is 1-4 bytes
        numeric = StructPrimitive(2, base_struct=byte, max_size=4)
        self.structs.append(numeric)
        # Floats (0-2^128-1), 8-bit floats are real I swear!
        floating_point = StructPrimitive(3, base_struct=byte, max_size=16)
        self.structs.append(floating_point)
        # Arrays are a dynamic container and are contextual
        # So, we leave them for the catalog to declare
    
    # Get a struct by data
    def get_struct(self, values):
        for struct in self.structs:
            if struct and struct.values == values:
                return struct
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

# Database commands
class DBCMD(IntFlag):
    # Getters
    GET_NEW_ID = 1 << 0
    GET_DATA = 1 << 1
    GET_STRUCT_DATA = 1 << 2
    GET_ID = 1 << 3
    GET_SUB_IDS = 1 << 4
    GET_STRUCTS = 1 << 5
    
    # Setters
    SET_DATA = 1 << 6
    SET_STRUCT = 1 << 7
    ADD_STRUCT = 1 << 8

# Container and handler which gets and sets data in the Struct Database File
class Database():
    def __init__(self, path):
        self.working_dir = path
        # Struct Database file containing all the structures
        self.sdb_path = os.path.join(self.working_dir, 'database.sdb')
        # Pointers file containing location data for individual structures, relevant for looking up stuff from the database file (quickly).
        self.ptrs_path = os.path.join(self.working_dir, 'pointers.sdb')
        
        # Init database
        if not os.path.exists(self.sdb_path):
            write_bytes(self.sdb_path)
        
        if not os.path.exists(self.ptrs_path):
            write_bytes(self.ptrs_path)
            
        self.struct_db = StructDatabase(self.sdb_path)
        
    CMDARGS = {
        DBCMD.GET_NEW_ID: (0, []),
        DBCMD.GET_DATA: (1, [int]),
        DBCMD.GET_STRUCT_DATA: (1, [object]),
        DBCMD.GET_ID: (1, [object]),
        DBCMD.GET_SUB_IDS: (1, [int]),
        DBCMD.GET_STRUCTS: (0, []),
        DBCMD.SET_DATA: (2, [int, object]),
        DBCMD.SET_STRUCT: (2, [int, object]),
        DBCMD.ADD_STRUCT: (1, [object]),
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

    # Retrieve ID by data
    def __getID__(self, data):
        try:
            return self.struct_db.structs.index(data)
        except:
            return None

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
        self.struct_db.structs.append(struct)
        
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
        elif cmd == DBCMD.GET_ID:
            return self.__getID__(args[0])
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