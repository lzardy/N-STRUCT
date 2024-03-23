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

def simplify_bits(bits):
    """Replaces groups of 0s with counts in an array of 0s and 1s."""
    bits_simplified = []
    count = 0
    for bit in bits:
        if bit == 0:
            count += 1
        else:
            if count > 1:
                bits_simplified.append(count)
            elif count == 1:
                bits_simplified.append(0)
            bits_simplified.append(bit)
            count = 0
    if count > 1:
        bits_simplified.append(count)
    elif count == 1:
        bits_simplified.append(0)
    return bits_simplified

bits_simplified = simplify_bits(bits)
print("Time elapsed: ", time.time() - last_time)
print("bits_simplified: ", len(bits_simplified))

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