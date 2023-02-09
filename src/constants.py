CACHE_DIR = ".working"
PUZZLE_DIR = "data/puzzles"
RESULTS_DIR = "benchmarks/"



# defines the puzzle sets to be tested.
# each puzzle set is a tuple of the following:
# (path to puzzle file, number of puzzles, number of lines per puzzle, number of lines between puzzles)
# The key will be used as the name of the test
PUZZLES = {
    "Standard": (f"{PUZZLE_DIR}/p096_sudoku.txt", 50, 9, 1),
    "Hard": (f"{PUZZLE_DIR}/top95", 95, 1, 0),
}

ROUND_AVG = 2