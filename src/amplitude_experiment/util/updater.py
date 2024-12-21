import random


def get_duration_with_jitter(duration: int, jitter: int):
    return max(0, duration + (random.randrange(-jitter, jitter) if jitter != 0 else 0))