import random
import statistics

import matplotlib.pyplot as plt

RUNS_NO = 10
MUTATION_PROBABILITY = 0.0075
POPULATION_SIZE = 50
ELITISM_RATIO = 0.1
SELECTION = "roulette" # "rank", "roulette"
EVALS_PER_DIM = 100
DIMENSIONS = (10, 30, 100)

SEED = 42

# objective functions
def one_max(representation: list[int]) -> int:
    return sum(representation)

def leading_ones(representation: list[int]) -> int:
    count = 0
    for bit in representation:
        if bit != 1:
            break
        count += 1
    return count

OBJECTIVES = {"One-max": one_max, "Leading ones": leading_ones}

class BinCandidate:
    def __init__(self, dimension=10, representation: list[int] | None = None) -> None:
        self.d = dimension
        if representation is None: # if not specified the bits are random
            representation = [random.randint(0, 1) for _ in range(dimension)]
        self.representation = representation
        self.fitness = 0

    def determine_fitness(self, objective=one_max):
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

def main():
    pass

if __name__ == "__main__":
    main()
