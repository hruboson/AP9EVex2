import math
import random
import statistics
import struct
from dataclasses import dataclass, replace
from typing import Any, Callable

import matplotlib.pyplot as plt

# algorithm configuration
RUNS_NO = 10
MUTATION_PROBABILITY = 0.0075
POPULATION_SIZE = 50
ELITISM_RATIO = 0.1
SELECTION = "roulette" # "rank", "roulette"
EVALUATIONS = 10000
DIMENSIONS = (10, )

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
    def _spin(candidates: list[BinCandidate], weights: list[float]) -> BinCandidate:
        pick = random.uniform(0., sum(weights))
        cumulative = 0.
        for candidate, weight in zip(candidates, weights):
            cumulative += weight
            if pick <= cumulative:
                return candidate
        return candidates[-1]

    def roulette(self) -> BinCandidate:
        worst_fitness = self.worst().fitness
        weights = [c.fitness - worst_fitness + EPSILON for c in self.candidates]
        return self._spin(self.candidates, weights)

    def rank(self) -> BinCandidate:
        ordered = sorted(self.candidates, key=lambda c: c.fitness)
        weights = [float(i) for i in range(1, len(ordered) + 1)]
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

    @classmethod
    def from_variant(cls, variant: Variant, function: TestFunction, dim: int, size: int) -> "BinPopulation":
        return cls([BinCandidate(dim * BITS_PER_DIM) for _ in range(size)])

    @staticmethod
    def objective(variant: Variant, function: TestFunction) -> Callable[[list[int]], float]:
        codec = CODECS[variant.representation](function, variant.boundary)
        return lambda bits: -function(codec.decode(bits))

class ConCandidate:
    def __init__(self, min: float, max: float, dimensions=10, representation: list[float] | None = None, mutation="gaussian", sigma: float = SIGMA, boundary: str = BOUNDARY) -> None:
        self.d = dimensions
        self.min = min
        self.max = max

        if representation is None: # if not specified the values are random
            representation = [random.uniform(min, max) for _ in range(dimensions)]
        self.representation = representation
        self.mutation = mutation
        self.fitness = 0
        self.sigma = sigma
        self.boundary = boundary

    def determine_fitness(self, objective):
        self.fitness = objective(self.representation)
        return self.fitness

    def crossover(self, other: ConCandidate, crossoverPoint: int) -> ConCandidate:
        child = self.representation[:crossoverPoint] + other.representation[crossoverPoint:]
        return ConCandidate(self.min, self.max, self.d, child, self.mutation, self.sigma, self.boundary)

    def mutate(self, sigma: float=SIGMA, probability: float=MUTATION_PROBABILITY):
        if random.random() < probability:
            dim_to_mutate = random.randrange(self.d)
            if self.mutation == "gaussian":
                value = random.gauss(self.representation[dim_to_mutate], self.sigma)
            else:
                value = random.uniform(self.min, self.max)
            
            self.representation[dim_to_mutate] = repair(value, self.min, self.max, self.boundary)

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
        weights = [float(i) for i in range(1, len(ordered) + 1)]
        return self._spin(ordered, weights)

    def select_parents(self, method: str = SELECTION) -> tuple[ConCandidate, ConCandidate]:
        select = self.roulette if method == "roulette" else self.rank
        first = select()
        second = select()
        for _ in range(10): # try to not select the same candidate twice
            if second is not first:
                break
            second = select()
        return first, second

    @classmethod
    def from_variant(cls, variant: Variant, function: TestFunction, dim: int, size: int) -> "ConPopulation":
        sigma = variant.sigma_ratio * (function.upper - function.lower)
        return cls([ConCandidate(function.lower, function.upper, dim, mutation=variant.mutation,
                                 sigma=sigma, boundary=variant.boundary)
                    for _ in range(size)])

    @staticmethod
    def objective(variant: Variant, function: TestFunction) -> Callable[[list[float]], float]:
        return function.as_fitness()

def bits_to_int(bits: list[int]) -> int:
    number = 0
    for bit in bits:
        number = (number << 1) | bit
    return number
 
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
    representation: str
    mutation_probability: float
    mutation: str = "gaussian"
    sigma_ratio: float = 0.05
    boundary: str = BOUNDARY

VARIANTS = [
    Variant("IEEE 754", "ieee754", MUTATION_PROBABILITY),
    Variant("Fixed-point", "fixed", MUTATION_PROBABILITY),
    Variant("BCD", "bcd", MUTATION_PROBABILITY),
    Variant("Real + Gaussian", "real", MUTATION_PROBABILITY, "gaussian"),
    Variant("Real + uniform", "real", MUTATION_PROBABILITY, "uniform"),
]

BIN_PROBABILITIES = (0.001, 0.0075, 0.02)
REAL_PROBABILITIES = (0.05, 0.2, 0.5, 1.0)
SIGMA_RATIOS = (0.01, 0.05, 0.1, 0.25)
SELECTIONS = ("roulette", "rank")


def elite_count() -> int:
    return max(1, round(ELITISM_RATIO * POPULATION_SIZE))


def build_population(variant: Variant, function: TestFunction, dim: int) -> tuple[Any, Callable[[Any], float]]:
    if variant.representation == "real":
        candidates = [ConCandidate(function.lower, function.upper, dim, mutation=variant.mutation)
                      for _ in range(POPULATION_SIZE)]
        return ConPopulation(candidates), function.as_fitness()
    codec = CODECS[variant.representation](function, variant.boundary)
    candidates = [BinCandidate(dim * BITS_PER_DIM) for _ in range(POPULATION_SIZE)]
    return BinPopulation(candidates), lambda bits: -function(codec.decode(bits))

def run_ga(variant: Variant, function: TestFunction, dim: int,
           selection: str = SELECTION, seed: int = SEED) -> list[float]:
    random.seed(seed)
    population_cls: Any = ConPopulation if variant.representation == "real" else BinPopulation
    population = population_cls.from_variant(variant, function, dim, POPULATION_SIZE)
    objective = population_cls.objective(variant, function)
    for candidate in population.candidates:
        candidate.determine_fitness(objective)

    n_elite = elite_count()
    offspring = POPULATION_SIZE - n_elite
    generations = max(1, (EVALUATIONS - POPULATION_SIZE) // offspring)
    history = [-population.best().fitness]

    for _ in range(generations):
        children = population.elite(n_elite)
        while len(children) < POPULATION_SIZE:
            p1, p2 = population.select_parents(selection)
            point = random.randint(1, len(p1.representation) - 1)
            child = p1.crossover(p2, point)
            child.mutate(variant.mutation_probability)
            child.determine_fitness(objective)
            children.append(child)
        population = population_cls(children, population.generation + 1)
        history.append(-population.best().fitness)
    return history


def run_experiment(function: TestFunction, dim: int, variants=VARIANTS,
                   selection: str = SELECTION) -> dict[str, list[list[float]]]:
    return {v.name: [run_ga(v, function, dim, selection, SEED + r) for r in range(RUNS_NO)]
            for v in variants}


def mean_std(histories: list[list[float]]) -> tuple[list[float], list[float]]:
    columns = list(zip(*histories))
    return ([statistics.mean(c) for c in columns],
            [statistics.stdev(c) for c in columns])


def plot_convergence(results: dict, path: str = "convergence.png") -> None:
    offspring = POPULATION_SIZE - elite_count()
    fig, axes = plt.subplots(len(TEST_FUNCTIONS), len(DIMENSIONS),
                             figsize=(12, 10), squeeze=False)
    for row, fname in enumerate(TEST_FUNCTIONS):
        for col, dim in enumerate(DIMENSIONS):
            ax = axes[row][col]
            for name, histories in results[(fname, dim)].items():
                mean, std = mean_std(histories)
                x = [POPULATION_SIZE + g * offspring for g in range(len(mean))]
                ax.plot(x, [max(m, 1e-12) for m in mean], label=name)
                ax.fill_between(x, [max(m - s, 1e-12) for m, s in zip(mean, std)],
                                [max(m + s, 1e-12) for m, s in zip(mean, std)], alpha=0.12)
            ax.set_yscale("log")
            ax.set_title(f"{fname}, d={dim}")
            ax.set_xlabel("evaluations")
            ax.set_ylabel("best f(x), mean +/- std")
            ax.grid(alpha=0.3)
    axes[0][0].legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)


def print_summary(results: dict) -> None:
    for (fname, dim), by_variant in results.items():
        print(f"\n{fname}, d={dim}")
        for name, histories in by_variant.items():
            finals = [h[-1] for h in histories]
            print(f"  {name:<18} mean {statistics.mean(finals):12.4f}  "
                  f"std {statistics.stdev(finals):10.4f}  best {min(finals):12.4f}")


def candidate_variants(base: Variant) -> list[Variant]:
    if base.representation != "real":
        return [replace(base, mutation_probability=p) for p in BIN_PROBABILITIES]
    sigmas = SIGMA_RATIOS if base.mutation == "gaussian" else (base.sigma_ratio,)
    return [replace(base, mutation_probability=p, sigma_ratio=s)
            for p in REAL_PROBABILITIES for s in sigmas]


def tune(function: TestFunction, dim: int = DIMENSIONS[0]) -> dict:
    best = {}
    for base in VARIANTS:
        scored = []
        for variant in candidate_variants(base):
            for selection in SELECTIONS:
                finals = [run_ga(variant, function, dim, selection, SEED + r)[-1]
                          for r in range(RUNS_NO)]
                scored.append((statistics.mean(finals), variant, selection))
        best[base.name] = min(scored, key=lambda s: s[0])
    return best


def main():
    results = {}
    for function in TEST_FUNCTIONS.values():
        for dim in DIMENSIONS:
            results[(function.name, dim)] = run_experiment(function, dim)
    print_summary(results)
    plot_convergence(results)

    for function in TEST_FUNCTIONS.values():
        print(f"\nBest parameters: {function.name}, d={DIMENSIONS[0]}")
        for name, (score, variant, selection) in tune(function).items():
            print(f"\t{name:<18} {score:12.4f}  p={variant.mutation_probability}  "
                  f"sigma_ratio={variant.sigma_ratio}  selection={selection}")
    plt.show()

if __name__ == "__main__":
    main()
