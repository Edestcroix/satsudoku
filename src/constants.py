CACHE_DIR = ".working"
PUZZLE_DIR = "data/puzzles"
RESULTS_DIR = "benchmarks/"

PUZZLES = {
    "Standard": (f"{PUZZLE_DIR}/p096_sudoku.txt", 50, 9, True),
    "Hard": (f"{PUZZLE_DIR}/top95", 95, 1, False),
}

ROUND_AVG = 2