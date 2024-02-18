import struct

# Converts an array of arbitrary data to bytes
def to_bytes(data):
    bytes_data = bytearray()
    for d in data:
        if isinstance(d, str):
            # Encode strings to bytes
            bytes_data.extend(d.encode('utf-8'))
        else:
            # Pack as  4-byte integer
            bytes_data.extend(struct.pack('I', d))
        # Zero byte for spacing
        bytes_data.extend([0] * 4)
    return bytes_data