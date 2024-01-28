import os
import zstandard as zstd
import cProfile

def read_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            yield os.path.join(root, file)

def compress_data():
    cctx = zstd.ZstdCompressor(level=3)
    for item in read_directory("C:/path/to/directory"):
        if os.path.isdir(item):
            compress_data(item)
        elif os.path.isfile(item):
            with open(item, 'rb') as f:
                data = f.read()
            compressed = cctx.compress(data)
        else:
            print(f"{item} is neither a file nor a directory, skipping.")

if __name__ == "__main__":
    cProfile.run('compress_data()')