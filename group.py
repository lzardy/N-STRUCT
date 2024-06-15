import argparse
import os
import time
import file_io
from file_io import write_bits

parser = argparse.ArgumentParser()
parser.add_argument('file_path', type=str, help='The path to the file to read')
args = parser.parse_args()

file_path = args.file_path
bits = file_io.read_bits(file_path)

print("bits: ", len(bits))

# Get current timestamp
last_time = time.time()

def simplify_bits(bits, ones=False, count_offset=0):
    """Replaces groups of 1s with counts in an array of 0s and 1s."""
    bits_simplified = []
    max_count = 0
    start_count = 1 + count_offset
    count = count_offset
    target_bit = 1 if ones else 0
    print("target_bit: ", target_bit)
    for bit in bits:
        if bit == target_bit:
            count += 1
        else:
            if count > start_count:
                bits_simplified.append(count)
                max_count = max(max_count, count)
            elif count == start_count:
                bits_simplified.append(target_bit)
            bits_simplified.append(bit)
            count = count_offset
    if count > start_count:
        bits_simplified.append(count)
        max_count = max(max_count, count)
    elif count == start_count:
        bits_simplified.append(target_bit)
    return bits_simplified, max_count

s_bits_zeros, max_zeros = simplify_bits(bits)
print("Time elapsed: ", time.time() - last_time)
print("s_bits_zeros len: ", len(s_bits_zeros))
print("s_bits_zeros (slice 0-10): ", s_bits_zeros[-10:])
print("max_zeros: ", max_zeros)

# Get current timestamp
last_time = time.time()

s_bits_ones, max_ones = simplify_bits(s_bits_zeros, True, max_zeros)
print("Time elapsed: ", time.time() - last_time)
print("s_bits_ones len: ", len(s_bits_ones))
print("s_bits_ones (slice 0-10): ", s_bits_ones[-10:])

current_directory = os.getcwd()
file_path = os.path.join(current_directory, "s_bits_ones")

# Any value between 2 and max_zeros is a 0, any value between max_zeros and max_ones is a 1
def s_bits_to_bits(s_bits, max_zeros):
    bits = []
    for val in s_bits:
        if val == 0:
            bits.append(0)
            continue
        if val == 1:
            bits.append(1)
            continue
        if val <= max_zeros:
            for _ in range(val):
                bits.append(0)
        else:
            for _ in range(val - max_zeros):
                bits.append(1)
    return bits

write_bits(file_path, s_bits_to_bits(s_bits_ones, max_zeros))

# TODO: Save s_bits to file directly instead of converting to bits (without increasing file size)

# Splits an array into chunks of specified size
def segment_array(data, num_vals):
    chunks = []
    for i in range(0, len(data), num_vals):
        chunk = []
        
        if num_vals == 1:
            chunk = [data[i]]
        else:
            chunk = data[i:i+num_vals]
        
        chunks.append(chunk)

    return chunks