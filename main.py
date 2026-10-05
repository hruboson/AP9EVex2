import random
import math
from dataclasses import dataclass
from typing import Callable

import matplotlib.pyplot as plt

RUNS_NO = 10
MUTATION_PROBABILITY = 0.0075
POPULATION_SIZE = 50
ELITISM_RATIO = 0.1
SELECTION = "roulette" # "rank", "roulette"
EVALS_PER_DIM = 100
DIMENSIONS = (10, 30, 100)

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
    pass

class ConPopulation:
    pass

def main():
    pass

if __name__ == "__main__":
    main()
