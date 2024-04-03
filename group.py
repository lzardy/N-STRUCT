import argparse
import time
import file_io

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

bits_simplified_first, max_count = simplify_bits(bits)
print("Time elapsed: ", time.time() - last_time)
print("bits_simplified_first: ", len(bits_simplified_first))
print("bits_simplified_first: ", bits_simplified_first[-10:])
print("max_count: ", max_count)

# Get current timestamp
last_time = time.time()

bits_simplified_second, max_count = simplify_bits(bits_simplified_first, True, max_count)
print("Time elapsed: ", time.time() - last_time)
print("bits_simplified_second: ", len(bits_simplified_second))
print("bits_simplified_second: ", bits_simplified_second[-10:])

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