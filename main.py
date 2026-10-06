import random
import struct
import math
from dataclasses import dataclass
from typing import Callable

import matplotlib.pyplot as plt

# algorithm configuration
RUNS_NO = 10
MUTATION_PROBABILITY = 0.0075
POPULATION_SIZE = 50
ELITISM_RATIO = 0.1
SELECTION = "roulette" # "rank", "roulette"
EVALS_PER_DIM = 100
DIMENSIONS = (10, 30, 100)

# continuous configuration
SIGMA = 3
EPSILON = 1e-9
REAL_DIM = 10
BOUNDARY = "clip"  # "clip", "wrap", "reflect"

# binary configuration
BITS_PER_DIM = 32

SEED = 42

# src: https://benchmarkfcns.info/generated/benchmarkfcns.schwefel.html
def schwefel(x: list[float]) -> float:
    return 418.9829 * len(x) - sum(xi * math.sin(math.sqrt(abs(xi))) for xi in x)

# src: https://benchmarkfcns.info/generated/benchmarkfcns.rastrigin.html
def rastrigin(x: list[float]) -> float:
    return 10 * len(x) + sum(xi ** 2 - 10 * math.cos(2 * math.pi * xi) for xi in x)

# src: https://benchmarkfcns.info/generated/benchmarkfcns.ackley.html
def ackley(x: list[float]) -> float:
    d = len(x)
    s1 = sum(xi ** 2 for xi in x) / d
    s2 = sum(math.cos(2 * math.pi * xi) for xi in x) / d
    return -20 * math.exp(-0.2 * math.sqrt(s1)) - math.exp(s2) + 20 + math.e

@dataclass(frozen=True)
class TestFunction:
    name: str
    function: Callable[[list[float]], float]
    lower: float
    upper: float
    optimum_value: float = 0.0

    def __call__(self, x: list[float]) -> float:
        return self.function(x)

    def clip(self, x: list[float]) -> list[float]:
        return [min(max(xi, self.lower), self.upper) for xi in x]

    def as_fitness(self) -> Callable[[list[float]], float]:
        return lambda x: -self.function(x)

SCHWEFEL = TestFunction("Schwefel", schwefel, -500.0, 500.0)
RASTRIGIN = TestFunction("Rastrigin", rastrigin, -5.12, 5.12)
ACKLEY = TestFunction("Ackley", ackley, -32.768, 32.768)

TEST_FUNCTIONS = {f.name: f for f in (SCHWEFEL, RASTRIGIN, ACKLEY)}

class BinCandidate:
    def __init__(self, dimension=10, representation: list[int] | None = None) -> None:
        self.d = dimension
        if representation is None: # if not specified the bits are random
            representation = [random.randint(0, 1) for _ in range(dimension)]
        self.representation = representation
        self.fitness = 0

    def determine_fitness(self, objective):
        self.fitness = objective(self.representation)
        return self.fitness

    def crossover(self, other: BinCandidate, crossoverPoint: int) -> BinCandidate:
        child = self.representation[:crossoverPoint] + other.representation[crossoverPoint:]
        return BinCandidate(self.d, child)

    def mutate(self, probability: float = MUTATION_PROBABILITY):
        for index in range(len(self.representation)):
            if random.uniform(0., 1.) < probability:
                self.representation[index] ^= 1  # XOR

class BinPopulation:
    def __init__(self, candidates: list[BinCandidate], generation: int = 0) -> None:
        self.candidates = candidates
        self.generation = generation

    def sorted_candidates(self) -> list[BinCandidate]:
        return sorted(self.candidates, key=lambda c: c.fitness, reverse=True)

    def best(self) -> BinCandidate:
        return max(self.candidates, key=lambda c: c.fitness)

    def worst(self) -> BinCandidate:
        return min(self.candidates, key=lambda c: c.fitness)

    def elite(self, count: int) -> list[BinCandidate]:
        return self.sorted_candidates()[:count]

    @staticmethod
    def _spin(candidates: list[BinCandidate], weights: list[int]) -> BinCandidate:
        pick = random.uniform(0., sum(weights))
        cumulative = 0.
        for candidate, weight in zip(candidates, weights):
            cumulative += weight
            if pick <= cumulative:
                return candidate
        return candidates[-1]

    def roulette(self) -> BinCandidate:
        weights = [c.fitness + 1 for c in self.candidates]
        return self._spin(self.candidates, weights)

    def rank(self) -> BinCandidate:
        ordered = sorted(self.candidates, key=lambda c: c.fitness)
        weights = list(range(1, len(ordered) + 1))
        return self._spin(ordered, weights)

    def select_parents(self, method: str = SELECTION) -> tuple[BinCandidate, BinCandidate]:
        select = self.roulette if method == "roulette" else self.rank
        first = select()
        second = select()
        for _ in range(10): # try to not select the same candidate twice
            if second is not first:
                break
            second = select()
        return first, second

class ConCandidate:
    def __init__(self, min: float, max: float, dimensions=10, representation: list[float] | None = None, mutation="gaussian") -> None:
        self.d = dimensions
        self.min = min
        self.max = max
        if representation is None: # if not specified the bits are random
            representation = [random.uniform(min, max) for _ in range(dimensions)]
        self.representation = representation
        self.mutation = mutation
        self.fitness = 0

    def determine_fitness(self, objective):
        self.fitness = objective(self.representation)
        return self.fitness

    def crossover(self, other: ConCandidate, crossoverPoint: int) -> ConCandidate:
        child = self.representation[:crossoverPoint] + other.representation[crossoverPoint:]
        return ConCandidate(self.min, self.max, self.d, child)

    def mutate(self, sigma: float=SIGMA, probability=MUTATION_PROBABILITY):
        if random.random() < probability:
            dim_to_mutate = random.randrange(self.d)
            if self.mutation == "gaussian":
                original_value = self.representation[dim_to_mutate]
                self.representation[dim_to_mutate] = random.gauss(original_value, sigma)
            else:
                self.representation[dim_to_mutate] = random.uniform(self.min, self.max)

class ConPopulation:
    def __init__(self, candidates: list[ConCandidate], generation: int = 0) -> None:
        self.candidates = candidates
        self.generation = generation

    def sorted_candidates(self) -> list[ConCandidate]:
        return sorted(self.candidates, key=lambda c: c.fitness, reverse=True)

    def best(self) -> ConCandidate:
        return max(self.candidates, key=lambda c: c.fitness)

    def worst(self) -> ConCandidate:
        return min(self.candidates, key=lambda c: c.fitness)

    def elite(self, count: int) -> list[ConCandidate]:
        return self.sorted_candidates()[:count]

    @staticmethod
    def _spin(candidates: list[ConCandidate], weights: list[float]) -> ConCandidate:
        pick = random.uniform(0., sum(weights))
        cumulative = 0.
        for candidate, weight in zip(candidates, weights):
            cumulative += weight
            if pick <= cumulative:
                return candidate
        return candidates[-1]

    def roulette(self) -> ConCandidate:
        worst_fitness = self.worst().fitness
        weights = [c.fitness - worst_fitness + EPSILON for c in self.candidates]
        return self._spin(self.candidates, weights)

    def rank(self) -> ConCandidate:
        ordered = sorted(self.candidates, key=lambda c: c.fitness)
        weights = list(range(1, len(ordered) + 1))
        weights_float = list(float(i) for i in weights)
        return self._spin(ordered, weights_float)

    def select_parents(self, method: str = SELECTION) -> tuple[ConCandidate, ConCandidate]:
        select = self.roulette if method == "roulette" else self.rank
        first = select()
        second = select()
        for _ in range(10): # try to not select the same candidate twice
            if second is not first:
                break
            second = select()
        return first, second

def repair(value: float, lower: float, upper: float, strategy: str = BOUNDARY) -> float:
    if math.isnan(value):
        return lower
    if math.isinf(value):
        return upper if value > 0 else lower
    width = upper - lower
    if strategy == "clip":
        return min(max(value, lower), upper)
    if strategy == "wrap":
        return lower + (value - lower) % width
    if strategy == "reflect":
        t = (value - lower) % (2 * width)
        return lower + (t if t <= width else 2 * width - t)
    raise ValueError(f"Unknown boundary strategy: {strategy}")
 
 
def bits_to_int(bits: list[int]) -> int:
    number = 0
    for bit in bits:
        number = (number << 1) | bit
    return number
 
 
class Codec:
    def __init__(self, function: TestFunction, boundary: str = BOUNDARY) -> None:
        self.function = function
        self.boundary = boundary
 
    def raw(self, gene: list[int]) -> float:
        raise NotImplementedError
 
    def decode(self, bits: list[int]) -> list[float]:
        genes = (bits[i:i + BITS_PER_DIM] for i in range(0, len(bits), BITS_PER_DIM))
        return [repair(self.raw(g), self.function.lower, self.function.upper, self.boundary)
                for g in genes]
 
 
class IEEE754Codec(Codec):
    def raw(self, gene: list[int]) -> float:
        return struct.unpack(">f", struct.pack(">I", bits_to_int(gene)))[0]
 
 
class FixedPointCodec(Codec):
    def __init__(self, function: TestFunction, boundary: str = BOUNDARY) -> None:
        super().__init__(function, boundary)
        width = function.upper - function.lower
        self.int_bits = max(1, math.ceil(math.log2(width + 1)))
        self.frac_bits = BITS_PER_DIM - self.int_bits
 
    def raw(self, gene: list[int]) -> float:
        return self.function.lower + bits_to_int(gene) / 2 ** self.frac_bits
 
 
class BCDCodec(Codec):
    DIGITS = BITS_PER_DIM // 4
 
    def __init__(self, function: TestFunction, boundary: str = BOUNDARY) -> None:
        super().__init__(function, boundary)
        width = function.upper - function.lower
        self.int_digits = len(str(math.ceil(width)))
        self.frac_digits = self.DIGITS - self.int_digits
 
    def raw(self, gene: list[int]) -> float:
        digits = [min(bits_to_int(gene[i:i + 4]), 9) for i in range(0, BITS_PER_DIM, 4)]
        number = int("".join(map(str, digits)))
        return self.function.lower + number / 10 ** self.frac_digits
 
 
CODECS = {"ieee754": IEEE754Codec, "fixed": FixedPointCodec, "bcd": BCDCodec}


@dataclass(frozen=True)
class Variant:
    name: str
    representation: str  # "ieee754", "fixed", "bcd", "real"
    mutation_probability: float
    mutation: str = "gaussian" # "gaussian", "uniform"
    # TODO

VARIANTS = [
    Variant("IEEE 754", "ieee754", MUTATION_PROBABILITY),
    Variant("Fixed-point", "fixed", MUTATION_PROBABILITY),
    Variant("BCD", "bcd", MUTATION_PROBABILITY),
    Variant("Real + Gaussian", "real", MUTATION_PROBABILITY, "gaussian"),
    Variant("Real + uniform", "real", MUTATION_PROBABILITY, "uniform"),
]
 
 
def run_ga():
    # TODO
    pass

def main():
    candidate = ConCandidate(-50, 50);
    print(candidate.representation)
    pass

if __name__ == "__main__":
    main()
