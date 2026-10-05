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

class Candidate:
    def __init__(self, dimension=10, representation: list[int] | None = None) -> None:
        self.d = dimension
        if representation is None: # if not specified the bits are random
            representation = [random.randint(0, 1) for _ in range(dimension)]
        self.representation = representation
        self.fitness = 0

    def determine_fitness(self, objective=one_max):
        self.fitness = objective(self.representation)
        return self.fitness

    def crossover(self, other: Candidate, crossoverPoint: int) -> Candidate:
        child = self.representation[:crossoverPoint] + other.representation[crossoverPoint:]
        return Candidate(self.d, child)

    def mutate(self, probability: float = MUTATION_PROBABILITY):
        for index in range(len(self.representation)):
            if random.uniform(0., 1.) < probability:
                self.representation[index] ^= 1  # XOR

class Population:
    def __init__(self, candidates: list[Candidate], generation: int = 0) -> None:
        self.candidates = candidates
        self.generation = generation

    def sorted_candidates(self) -> list[Candidate]:
        return sorted(self.candidates, key=lambda c: c.fitness, reverse=True)

    def best(self) -> Candidate:
        return max(self.candidates, key=lambda c: c.fitness)

    def worst(self) -> Candidate:
        return min(self.candidates, key=lambda c: c.fitness)

    def elite(self, count: int) -> list[Candidate]:
        return self.sorted_candidates()[:count]

    @staticmethod
    def _spin(candidates: list[Candidate], weights: list[int]) -> Candidate:
        pick = random.uniform(0., sum(weights))
        cumulative = 0.
        for candidate, weight in zip(candidates, weights):
            cumulative += weight
            if pick <= cumulative:
                return candidate
        return candidates[-1]

    def roulette(self) -> Candidate:
        weights = [c.fitness + 1 for c in self.candidates]
        return self._spin(self.candidates, weights)

    def rank(self) -> Candidate:
        ordered = sorted(self.candidates, key=lambda c: c.fitness)
        weights = list(range(1, len(ordered) + 1))
        return self._spin(ordered, weights)

    def select_parents(self, method: str = SELECTION) -> tuple[Candidate, Candidate]:
        select = self.roulette if method == "roulette" else self.rank
        first = select()
        second = select()
        for _ in range(10): # try to not select the same candidate twice
            if second is not first:
                break
            second = select()
        return first, second

def print_stats(results: list[float], label: str = ""):
    print(f"{label:<24} best={max(results):7.2f}  worst={min(results):7.2f}  "
          f"mean={statistics.mean(results):7.2f}  median={statistics.median(results):7.2f}  "
          f"std={statistics.pstdev(results):6.2f}")

# single run
def run_ga(objective, dimension: int, max_evals: int,
           pop_size: int = POPULATION_SIZE,
           elitism: float = ELITISM_RATIO,
           mutation: float = MUTATION_PROBABILITY,
           selection: str = SELECTION):
    history: list[int] = []
    best_so_far = -1

    def evaluate(candidate: Candidate):
        nonlocal best_so_far
        candidate.determine_fitness(objective)
        best_so_far = max(best_so_far, candidate.fitness)
        history.append(best_so_far)

    # starting population
    candidates = [Candidate(dimension) for _ in range(min(pop_size, max_evals))]
    for candidate in candidates:
        evaluate(candidate)
    population = Population(candidates)

    # new population: elites + children
    n_elite = max(0, min(round(elitism * pop_size), pop_size - 2))
    while len(history) < max_evals:
        new_candidates = population.elite(n_elite)  # do not evaluate the elites

        while len(new_candidates) < pop_size and len(history) < max_evals:
            parent_a, parent_b = population.select_parents(selection)
            point = random.randint(1, dimension - 1)

            for child in (parent_a.crossover(parent_b, point),
                          parent_b.crossover(parent_a, point)):
                if len(new_candidates) >= pop_size or len(history) >= max_evals:
                    break
                child.mutate(mutation)
                evaluate(child)
                new_candidates.append(child)
        population = Population(new_candidates, population.generation + 1)

    return best_so_far, history, population

def run_experiment(objective, dimension: int, runs: int = RUNS_NO, **params):
    max_evals = EVALS_PER_DIM * dimension
    results, histories = [], []
    for _ in range(runs):
        best, history, _ = run_ga(objective, dimension, max_evals, **params)
        results.append(best)
        histories.append(history)
    average_history = [statistics.mean(h[i] for h in histories) for i in range(max_evals)]
    return results, average_history

def plot_results(curves: dict[str, dict[int, list[float]]],
                 all_results: dict[str, dict[int, list[float]]],
                 params: dict):
    problems = list(curves)
    n_rows, n_cols = len(problems), len(DIMENSIONS)
 
    fig = plt.figure(figsize=(15, 4 * n_rows + 3.6))
    grid = fig.add_gridspec(n_rows + 1, n_cols, height_ratios=[4] * n_rows + [3.2])
 
    # convergence graphs
    for row, name in enumerate(problems):
        for col, dimension in enumerate(DIMENSIONS):
            ax = fig.add_subplot(grid[row, col])
            curve = curves[name][dimension]
            ax.plot(range(1, len(curve) + 1), curve, color="red" if name == "One-max" else "tab:blue", label="mean of best-so-far")
            ax.axhline(dimension, color="gray", linestyle="--", linewidth=0.8, label="optimum")
            ax.set_title(f"{name} - {dimension}D")
            ax.set_xlabel("Evalutaions")
            ax.set_ylabel(f"Average best fitness ({RUNS_NO} runs)")
            ax.grid(True, alpha=0.3)
            ax.legend(loc="lower right")
 
    # statistics table
    ax_table = fig.add_subplot(grid[n_rows, :])
    ax_table.axis("off")
    columns = ["Problem", "Dimension", "Evaluations", "Best", "Worst",
               "Mean", "Median", "Std. dev."]
    rows = []
    for name in problems:
        for dimension in DIMENSIONS:
            r = all_results[name][dimension]
            rows.append([name, f"{dimension}D", EVALS_PER_DIM * dimension,
                         f"{max(r):.0f}", f"{min(r):.0f}",
                         f"{statistics.mean(r):.2f}", f"{statistics.median(r):.1f}",
                         f"{statistics.pstdev(r):.2f}"])
    table = ax_table.table(cellText=rows, colLabels=columns, loc="center",
                           cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    for (row, col), cell in table.get_celld().items():
        if row == 0: # header
            cell.set_facecolor("#dbe5f1")
            cell.set_text_props(fontweight="bold")
        elif (row - 1) // n_cols % 2 == 1: # shade the second problem
            cell.set_facecolor("#f4f4f4")
 
    fig.suptitle(f"Genetic algorithm - population {params['pop_size']}, "
                 f"elitism {params['elitism']:.0%}, {params['selection']} selection, "
                 f"mutation {params['mutation']:.2%}, one-point crossover",
                 fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig("convergence_results.png", dpi=150)

def main():
    random.seed(SEED)
    params = dict(pop_size=POPULATION_SIZE, elitism=ELITISM_RATIO,
                  mutation=MUTATION_PROBABILITY, selection=SELECTION)
    print("Parameters used:", params, "\n")
 
    curves, all_results = {}, {}
    for name, objective in OBJECTIVES.items():
        print(f"=== {name} ===")
        curves[name], all_results[name] = {}, {}
        for dimension in DIMENSIONS: # 10D, 30D, 100D
            results, curves[name][dimension] = run_experiment(objective, dimension, RUNS_NO, **params)
            all_results[name][dimension] = results
            print_stats(results, f"{dimension}D ({EVALS_PER_DIM * dimension} evals)")
        print()
 
    plot_results(curves, all_results, params)
 
    if "agg" not in plt.get_backend().lower():
        plt.show()

if __name__ == "__main__":
    main()
