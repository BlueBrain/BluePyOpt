"""BluePyOpt tools"""

import hashlib


def uint32_seed(string):
    """Get unsigned int seed of a string"""

    hex_value = hashlib.md5(string).hexdigest()

    return int(hex_value, 16) & 0xFFFFFFFF
