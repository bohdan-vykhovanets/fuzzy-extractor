import random

import numpy as np
import hashlib
import os

class FuzzyExtractor:
    def __init__(self, k, v, t):
        self.k = k
        self.v = v
        self.t = t

    def generate(self, bio, l):
        salt = os.urandom(l)
        sketch, sketch_hash = self.sketch(bio)

        hasher = hashlib.new('sha256')
        hasher.update(bio)
        hasher.update(salt)
        key = hasher.digest()

        return key, sketch, sketch_hash, salt # R, s, h, r

    def reproduce(self, bio, sketch, sketch_hash, salt):
        reconstructed = self.reconstruct(bio, sketch, sketch_hash)
        if reconstructed == 0:
            return 0

        hasher = hashlib.new('sha256')
        hasher.update(reconstructed)
        hasher.update(salt)
        key = hasher.digest()

        return key

    def sketch(self, bio):
        sketch = np.zeros_like(bio)
        intervals = np.zeros_like(bio)

        for i in range(len(bio)):
            if bio[i] % self.k == 0:
                c = random.choice([-1, 1])
                sketch[i] = c * self.k / 2
                continue

            intervals[i] = bio[i] - (bio[i] % self.k) + (self.k / 2)
            sketch[i] = intervals[i] - bio[i]

        hasher = hashlib.new('sha256')
        hasher.update(bio.tobytes())
        hasher.update(sketch.tobytes())

        return sketch.tobytes(), hasher.digest()

    def reconstruct(self, new_bio, sketch, old_hash):  # y, s
        sketch = np.frombuffer(sketch, dtype=int)
        old_bio = np.zeros_like(new_bio)               # z
        new_intervals = np.zeros_like(new_bio)         # I
        old_intervals = np.zeros_like(new_bio)         # y'

        for i in range(len(new_bio)):
            old_intervals[i] = new_bio[i] + sketch[i]

            new_intervals[i] = old_intervals[i] - (old_intervals[i] % self.k) + (self.k / 2)
            if abs(new_intervals[i] - old_intervals[i]) > self.t:
                return 0 # return zero as indication of failure

            old_bio[i] = new_intervals[i] - sketch[i]

        hasher = hashlib.new('sha256')
        hasher.update(old_bio.tobytes())
        hasher.update(sketch.tobytes())

        if hasher.digest() != old_hash:
            return 0 # return zero as indication of failure

        return old_bio.tobytes()
