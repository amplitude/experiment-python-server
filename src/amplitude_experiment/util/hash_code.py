import hashlib


def hash_code(string) -> int:
    return hashlib.md5(string.encode('utf-8')).hexdigest()[:32]
