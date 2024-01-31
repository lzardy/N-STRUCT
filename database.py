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
    BLUEPRINT = 3

# TODO: Implement an approach for Lempel-Ziv-Welch Compression

# Details what other structs make up a struct
class StructBase:
    def __init__(self, id=None, substructs=[], struct_type=STYPE.BASE):
        self.id = id
        self.substructs = substructs
        self.type = struct_type
    
    # Adds a substruct to this struct
    def add_substruct(self, substruct):
        self.substructs.append(substruct)
    
    # Returns a copy of this struct
    def copy(self):
        return StructBase(self.id, self.substructs.copy(), self.type)

# TODO: Represents a struct through a data operation between some number of structs
# class StructDelta:

# Details the raw byte data that represents a struct and its substructs
# Should only be kept in memory when actively being used
class StructData(StructBase):
    def __init__(self, id=None, substructs=[], data=[], num_values=1, struct_type=STYPE.DATA):
        super().__init__(id, substructs, struct_type)
        self.data = data
        # Number of possible values this struct can represent (from 0)
        self.num_values = num_values
    
    # Returns a list of all possible values this struct can represent
    def get_values(self):
        values = []
        for value in range(self.num_values):
            values.append(value)
    
    def copy(self):
        return StructData(self.id, self.substructs.copy(), self.data.copy(), self.num_values, self.type)

# A unique struct built using other structs
# Ex: Byte structs are 8 bits
class StructPrimitive(StructData):
    def __init__(self, id=None, substructs=[], data=[], base_struct=None, max_size=1, step_size=0, num_values=1, struct_type=STYPE.PRIMITIVE):
        super().__init__(id, substructs, data, num_values, struct_type)
        self.base_struct = base_struct
        self.max_size = max_size
        self.step_size = step_size
        self.max_value = num_values ** self.max_size
        if self.base_struct:
            self.max_value = self.num_values * (self.base_struct.num_values ** self.max_size)
            self.fill_substructs()
    
    # Calculates the maximum size the data of this struct can be
    def get_total_size(self):
        if self.base_struct:
            return self.max_size * self.base_struct.get_total_size()
        return self.max_size

    # Fills substructs array with copies of base_struct
    def fill_substructs(self):
        for i in range(self.max_value):
            self.substructs.append(self.base_struct.copy())
        
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
        self.structs = []
        
        self.default_fill()
    
    # Fills structs array with default structures (bit, byte, integer, float, etc.)
    def default_fill(self):
        # Bits (0 or 1)
        bit = self.structs.append(StructPrimitive(0, num_values=2))
        # Bytes (0-255)
        byte = self.structs.append(StructPrimitive(1, base_struct=bit, max_size=8))
        

# Database commands
class DBCMD(IntFlag):
    # Getters
    GET_NEW_ID = 1 << 0
    GET_DATA = 1 << 1
    GET_ID = 1 << 2
    GET_SUB_IDS = 1 << 3
    
    # Setters
    SET_DATA = 1 << 4
    SET_ID = 1 << 5

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
        DBCMD.GET_ID: (1, [object]),
        DBCMD.GET_SUB_IDS: (1, [int]),
        DBCMD.SET_DATA: (2, [int, object]),
        DBCMD.SET_ID: (2, [object, int]),
    }

    # Gets and reserves the next ID for a new struct
    # Essentially appends a new struct to the end of the database file
    def __getNewID__(self):
        new_id = len(self.struct_db.structs)
        self.struct_db.structs.append(None)
        
        return new_id

    # Retrieve data by ID
    def __getData__(self, id):
        return self.struct_db.structs[id]

    # Retrieve ID by data
    def __getID__(self, data):
        return self.struct_db.structs.index(data)

    # Retrieve substruct IDs in given struct
    def __getSubIDs__(self, id):
        return self.struct_db.structs[id].substructs
    
    # Assigns data to a given ID
    def __setData__(self, id, data):
        struct = self.struct_db.structs[id]
        if struct.type != STYPE.DATA:
            self.struct_db.structs[id] = StructData(id, struct.substructs, data)
    
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
    def query(self, cmd, *args):
        self.__checkCMD__(cmd, args)
        
        if cmd == DBCMD.GET_NEW_ID:
            return self.__getNewID__(self)
        elif cmd == DBCMD.GET_DATA:
            return self.__getData__(self, args[0])
        elif cmd == DBCMD.GET_ID:
            return self.__getID__(self, args[0])
        elif cmd == DBCMD.GET_SUB_IDS:
            return self.__getSubIDs__(self, args[0])
        elif cmd == DBCMD.SET_DATA:
            return self.__setData__(self, args[0], args[1])
        elif cmd == DBCMD.SET_ID:
            return self.__setID__(self, args[0], args[1])