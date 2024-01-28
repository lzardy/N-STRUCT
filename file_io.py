import os
from error_handler import handle_errors

BYTE_BITS = 8

@handle_errors
def read_bits(file_path):
    data = []
    with open(file_path, 'rb') as file:
        byte = file.read(1)
        while byte:
            for i in range(BYTE_BITS):
                data.append(bool((ord(byte) >> (7 - i)) & 1))
            byte = file.read(1)
    return data

@handle_errors
def write_bits(file_path, data):
    with open(file_path, 'wb') as file:
        for i in range(0, len(data), BYTE_BITS):
            byte = sum([int(data[j]) << (7 - j % BYTE_BITS) for j in range(i, min(i + BYTE_BITS, len(data)))])
            file.write(bytes([byte]))

@handle_errors
def read_bytes(file_path, callback=None):
    with open(file_path, 'rb') as file:
        if callback:
            while True:
                byte = file.read(1)
                if not byte:
                    break
                callback(byte)
        else:
            data = file.read()
    return data if not callback else None

@handle_errors
def write_bytes(file_path, data=None):
    dir_name = os.path.dirname(file_path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    with open(file_path, 'wb') as file:
        if data:
            file.write(data)

@handle_errors
def read(file_path, callback=None):
    with open(file_path, 'r') as file:
        if callback:
            for line in file:
                callback(line)
        else:
            data = file.read()
    return data if not callback else None

@handle_errors
def write(file_path, data):
    dir_name = os.path.dirname(file_path)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    with open(file_path, 'w') as file:
        file.write(data)