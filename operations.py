from enum import IntFlag
from error_handler import handle_errors

class FILEOP(IntFlag):
    REFINE = 1 << 0
    SIMPLIFY = 1 << 1
    CONVERT = 1 << 2

@handle_errors
def do(path, operation=FILEOP.REFINE):
    if operation & FILEOP.REFINE:
        pass
    elif operation & FILEOP.SIMPLIFY:
        pass
    elif operation & FILEOP.CONVERT:
        pass
    else:
        raise ValueError("Invalid operation")