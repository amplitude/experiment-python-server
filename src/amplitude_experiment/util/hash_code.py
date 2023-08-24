def hash_code(string) -> int:
    hash_value = 0
    if len(string) == 0:
        return hash_value
    for char in string:
        chr_code = ord(char)
        hash_value = ((hash_value << 5) - hash_value) + chr_code
        hash_value &= 0xFFFFFFFF
    return hash_value
