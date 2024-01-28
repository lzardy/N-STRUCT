from enum import IntFlag
import os
from error_handler import handle_errors
from file_io import read_bits, write_bits, read_bytes, write_bytes

# TODO: Utilize ZStandard Compression

from enum import Enum

# Struct types
class STYPE(Enum):
    COUNT = 0
    BASE = 1
    DATA = 2
    BLUEPRINT = 3

# TODO: Implement an approach for Lempel-Ziv-Welch Compression

# Represents a struct repeated a certain number of times
# A class-based approach to Run-Length Encoding compression
class StructCount:
    def __init__(self, id=None, refID=None, count=0, size=None, struct_type=STYPE.COUNT):
        self.id = id
        self.refID = refID
        self.count = count
        self.type = struct_type
        # TODO: Add self.size, which grabs the len() of the data for the StructData with this ID
    
    def add(self, val):
        self.count += val
    
    def subtract(self, val):
        self.count -= val

# Details what other structs make up this struct
class StructBase:
    def __init__(self, id=None, substructs=[], struct_type=STYPE.BASE):
        self.id = id
        self.substructs = substructs
        self.type = struct_type
    
    def add_substruct(self, substruct):
        self.substructs.append(substruct)

# TODO: Represents a struct through a data operation between some number of structs
# class StructDelta:

# Details the raw byte data that represents a struct and its substructs
# Should only be kept in memory when actively being used
class StructData(StructBase):
    def __init__(self, id=None, substructs=[], data=[], struct_type=STYPE.DATA):
        super().__init__(id, substructs, struct_type)
        self.data = data
        self.size = len(self.data)

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
        
        # Init empty database
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
        pass

    # Retrieve data by ID
    def __getData__(self, id):
        pass

    # Retrieve ID by data
    def __getID__(self, data):
        pass

    # Retrieve substruct IDs in given struct
    def __getSubIDs__(self, id):
        pass
    
    # Assigns data to a given ID
    def __setData__(self, id, data):
        # TODO: Use write_bits to 
        pass
    
    # Assigns an ID to the given data
    def __setID__(self, data, id):
        pass
    
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