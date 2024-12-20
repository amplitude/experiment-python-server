C1_32 = 0xcc9e2d51
C2_32 = 0x1b873593
R1_32 = 15
R2_32 = 13
M_32 = 5
N_32 = 0xe6546b64


def hash32x86(input_str: str, seed: int = 0) -> int:
    """Calculate 32-bit Murmur3 hash of a string."""
    data = input_str.encode('utf-8')
    length = len(data)
    n_blocks = length // 4
    hash_val = seed

    # body
    for i in range(n_blocks):
        index = i * 4
        k = read_int_le(data, index)
        hash_val = mix32(k, hash_val)

    # tail
    index = n_blocks * 4
    k1 = 0
    remaining = length - index

    if remaining == 3:
        k1 ^= data[index + 2] << 16
        k1 ^= data[index + 1] << 8
        k1 ^= data[index]
        k1 = (k1 * C1_32) & 0xffffffff
        k1 = rotate_left(k1, R1_32)
        k1 = (k1 * C2_32) & 0xffffffff
        hash_val ^= k1
    elif remaining == 2:
        k1 ^= data[index + 1] << 8
        k1 ^= data[index]
        k1 = (k1 * C1_32) & 0xffffffff
        k1 = rotate_left(k1, R1_32)
        k1 = (k1 * C2_32) & 0xffffffff
        hash_val ^= k1
    elif remaining == 1:
        k1 ^= data[index]
        k1 = (k1 * C1_32) & 0xffffffff
        k1 = rotate_left(k1, R1_32)
        k1 = (k1 * C2_32) & 0xffffffff
        hash_val ^= k1

    hash_val ^= length
    return fmix32(hash_val)


def mix32(k: int, hash_val: int) -> int:
    """Mix function for Murmur3."""
    k = (k * C1_32) & 0xffffffff
    k = rotate_left(k, R1_32)
    k = (k * C2_32) & 0xffffffff
    hash_val ^= k
    hash_val = rotate_left(hash_val, R2_32)
    hash_val = (hash_val * M_32 + N_32) & 0xffffffff
    return hash_val


def fmix32(hash_val: int) -> int:
    """Final mix function for Murmur3."""
    hash_val ^= hash_val >> 16
    hash_val = (hash_val * 0x85ebca6b) & 0xffffffff
    hash_val ^= hash_val >> 13
    hash_val = (hash_val * 0xc2b2ae35) & 0xffffffff
    hash_val ^= hash_val >> 16
    return hash_val


def rotate_left(x: int, n: int, width: int = 32) -> int:
    """Rotate a number left by n bits."""
    n = n % width if n > width else n
    mask = (0xffffffff << (width - n)) & 0xffffffff
    r = ((x & mask) >> (width - n)) & 0xffffffff
    return ((x << n) | r) & 0xffffffff

def read_int_le(data: bytes, index: int = 0) -> int:
    """Read a little-endian 32-bit integer from bytes."""
    n = (data[index] << 24) | (data[index + 1] << 16) | \
        (data[index + 2] << 8) | data[index + 3]
    return reverse_bytes(n)

def reverse_bytes(n: int) -> int:
    """Reverse the bytes of a 32-bit integer."""
    return (((n & 0xff000000) >> 24) |
            ((n & 0x00ff0000) >> 8) |
            ((n & 0x0000ff00) << 8) |
            ((n & 0x000000ff) << 24)) & 0xffffffff
