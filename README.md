# AP9EV excercise 2

Project for the Evolutionary Computation Techniques class. Second assignment.

Author: [Ondřej Hruboš](https://github.com/hruboson), [Github repository](https://github.com/hruboson/AP9EVex2)

This implementation builds on the algorithm and object-oriented implementation of the first assignment, while adding new classes representing the continuous implementation.

**Test functions** (minimisation, 10D, in `TestFunction` objects so any algorithm can be substituted): Schwefel ([-500, 500]), Rastrigin ([-5.12, 5.12]) and Ackley ([-32.768, 32.768]).

**Binary representations** (32 bits per dimension, decoded by a `Codec`):
- **IEEE 754:** the 32 bits are interpreted as a float32.
- **Fixed-point:** `ceil(log2(range + 1))` bits for the integer part, the rest for the fraction, offset to the lower bound.
- **BCD:** 8 decimal digits of 4 bits each, offset to the lower bound. Groups above 9 are clamped to 9.

All codecs repair values outside the allowed interval with a boundary strategy (`clip`, `wrap` or `reflect`, switched by `BOUNDARY` constant). NaN and infinity are mapped to the bounds. The results below use `clip`.

**Real-valued GA:** one-point crossover on the level of whole dimensions, and one of two mutations that change one random dimension with probability `p`:
- **Gaussian:** a new value drawn from N(old value, sigma), with sigma = `sigma_ratio * range`.
- **Uniform:** a new value drawn uniformly from the allowed range.

Mutated values are repaired with the same boundary strategy.

**GA setup:** population 50, 10 % elitism, roulette (shifted by the worst fitness, because the fitness is `-f(x)`) or rank selection, one-point crossover, 10 000 evaluations per run, 10 runs per variant (seeds `SEED + run`). `tune()` runs a grid search over mutation probability, sigma ratio and selection at d=10.

# Experiments

The algorithm runs 10 000 times for each test functions and problem in 10 dimensions.

At the end I try to find the best hyperparameter settings by running the algorithm using different variants of hyperparameters. Best results for each test function and problem are shown. You can find example output in the [`out.txt`](./out.txt) file.

> [!NOTE]
> Due to time and HW constrains I did not autotune for every single parameters, but for selected ones.

# Results

Convergence graph (means of 10 runs, **logarithmic scale**):

![Convergence graph](convergence.png)

Final best f(x) after 10 000 evaluations, 10D. Values are the tuned results (best of the hyperparameter grid, mean of 10 runs). The full output with default parameters is in [`out.txt`](./out.txt).

| Method | Schwefel | Rastrigin | Ackley | Best parameters |
|---|---:|---:|---:|---|
| IEEE 754 | 1855.13 | 0.00 | 0.00 | p=0.001, roulette (Schwefel: p=0.02) |
| Fixed-point | 223.95 | 4.41 | 2.17 | p=0.02, rank (Ackley: p=0.0075) |
| BCD | 341.45 | 33.96 | 7.68 | p=0.02, rank (Schwefel: p=0.0075) |
| Real + Gaussian | 594.42 | 18.99 | 7.10 | p=0.05, sigma_ratio=0.01, rank |
| Real + uniform | 610.64 | 27.31 | 10.46 | p=0.05, rank or roulette |


- **IEEE 754:** good for Rastrigin and Ackley, but the worst on Schwefel. Float32 is densest around 0, which is where the functions have their optimum.
- **Fixed-point:** the most consistent method and the best for Schwefel.
- **BCD:** good only for Schwefel. 
- **Real + Gaussian:** better than uniform on all three functions. Small sigma was better for most cases and a low mutation probability, but it was still worse than fixed-point, probably because it mutates at most one gene per child.
- **Real + uniform:** the weakest on Ackley and Rastrigin among the unbiased methods.

#### Output shown as table

##### Schwefel, d=10

| Method | Mean | Std | Best |
|---|---:|---:|---:|
| IEEE 754 | 2124.6609 | 198.0172 | 1807.6239 |
| Fixed-point | 404.2138 | 178.2633 | 81.8457 |
| BCD | 692.9258 | 548.5380 | 2.0123 |
| Real + Gaussian | 623.7102 | 219.3024 | 134.3633 |
| Real + uniform | 651.5189 | 266.6609 | 237.7958 |

##### Rastrigin, d=10

| Method | Mean | Std | Best |
|---|---:|---:|---:|
| IEEE 754 | 0.0000 | 0.0000 | 0.0000 |
| Fixed-point | 4.9694 | 3.7018 | 0.0634 |
| BCD | 38.1964 | 25.1454 | 13.2318 |
| Real + Gaussian | 22.5406 | 6.9665 | 12.6198 |
| Real + uniform | 27.3068 | 6.6001 | 16.3573 |

##### Ackley, d=10

| Method | Mean | Std | Best |
|---|---:|---:|---:|
| IEEE 754 | 0.0000 | 0.0000 | 0.0000 |
| Fixed-point | 2.3461 | 0.6016 | 1.1716 |
| BCD | 9.2296 | 1.9285 | 5.7320 |
| Real + Gaussian | 7.7079 | 2.7714 | 4.7031 |
| Real + uniform | 10.4612 | 1.1815 | 8.6814 |


### Optimal hyperparameters for each test function and solved problem

##### Best parameters: Schwefel, d=10

| Method | Value | p | sigma_ratio | selection |
|---|---:|---:|---:|---|
| IEEE 754 | 1855.1286 | 0.02 | 0.05 | roulette |
| Fixed-point | 223.9531 | 0.02 | 0.05 | rank |
| BCD | 341.4462 | 0.0075 | 0.05 | rank |
| Real + Gaussian | 594.4231 | 0.05 | 0.01 | rank |
| Real + uniform | 610.6386 | 0.05 | 0.05 | rank |

##### Best parameters: Rastrigin, d=10

| Method | Value | p | sigma_ratio | selection |
|---|---:|---:|---:|---|
| IEEE 754 | 0.0000 | 0.001 | 0.05 | roulette |
| Fixed-point | 4.4126 | 0.02 | 0.05 | rank |
| BCD | 33.9558 | 0.02 | 0.05 | rank |
| Real + Gaussian | 18.9872 | 0.05 | 0.01 | roulette |
| Real + uniform | 27.3068 | 0.05 | 0.05 | roulette |

##### Best parameters: Ackley, d=10

| Method | Value | p | sigma_ratio | selection |
|---|---:|---:|---:|---|
| IEEE 754 | 0.0000 | 0.001 | 0.05 | roulette |
| Fixed-point | 2.1700 | 0.0075 | 0.05 | rank |
| BCD | 7.6800 | 0.02 | 0.05 | rank |
| Real + Gaussian | 7.0994 | 0.05 | 0.05 | rank |
| Real + uniform | 10.4612 | 0.05 | 0.05 | roulette |

## Run

- Either use the prepared [`nix`](./shell.nix) shell file:
    - Install [`nix`](https://nixos.org/download/) on your system (currently only for Linux/MacOS)
    - Enter the shell: `nix-shell ./shell.nix`
    - Run the Python script: `python ./main.py`
- Use your own installation of **Python 3.14** (older versions will most likely not work due to the usage of type hints!)
    - Create a virtual environment with the attached [`requirements.txt`](./requirements.txt): 
        - Windows: `python -m venv .venv && .venv\\Scripts\\activate && pip install -r requirements.txt`
        - Linux/MacOS: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
    - Run the Python script: `python ./main.py`
    - Leave virtual environment: `deactivate`
