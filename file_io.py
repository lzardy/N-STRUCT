import os
from error_handler import handle_errors

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