# Satsudoku
A sudoku SAT solver

## Scripts
The following scrips can be used to solve sudoku puzzles using `minisat`. Both
are just wrappers to get input and call the driver code in `src/`
### sud2sat
Converts a sudoku puzzle read from stdin into CNF format and outputs to stdout.
Can parse sudoku puzzles in any format where empty cells are denoted by a consistent character (e.g. `0`, `.` or `_`), and cells are not separated by anything other than whitespace. `sud2sat` assumes the first non-digit character or `0` it encounters after stripping all whitespace is the empty cell character. Only 9x9 puzzles are supported. Since a large portion of the CNF encodings are identical for every sudoku puzzle, `sud2sat` looks for files containing this portion in `data/`, creating them if not found, and then concatenates them with the puzzle-specific CNF. This means that the first time `sud2sat` is run on a puzzle, it will take longer if `data/` is deleted.
### sat2sud
Converts the satifiablility output from `minisat`, read from stdin, into a solved sudoku puzzle.
Only 9x9 puzzles are supported. The input must be in the format output by `minisat` ran on a CNF file generated by `sud2sat`, and it must be a satisfying assignment. (i.e the starting sudoku puzzle had a solution) A solved puzzle will look like this:  

483 921 657  
967 345 821   
251 876 493   

548 132 976  
729 564 138   
136 798 245   
 
372 689 514   
814 253 769   
695 417 382  

## Benchmarking
The `benchmark` script runs the same encoding functions in `src/` as sud2sat on puzzles from `data/puzzles` and gathers benchmarking data from `minisat` solving these puzzles. 
### Usage
-  `-s --silent` prevents printing to stdout.
- `-t=[] --test=[]` specify testing standard or hard puzzles, defaults to standard when not specified
- `-e=[] --enc=[]` specify the CNF encoding to use, will default to the minimal encoding when not specified. Can be one of either min/minimal, eff/efficient, or ext/extended. (e.g `-e=min` or `-e=extended`)
- `-a --all` tests all encodings with both standard and hard puzzles. Outputs results to `benchmarks` directory.
- `-k --keep` keeps the CNF files generated by sud2sat and the solution encodings from `minisat`. By default, these files are deleted after `minisat` has finished solving them. These will be stored in the `benchmarks/encodings` and `benchmarks/solutions` directories, respectively.
- `-S --summarize` can only be used with `-a`. Outputs a summary of the benchmarking results to `benchmarks/summary.md`. This will contain the averages of decisions, decision rate, propagations, propagation rates, and CPU time for each encoding, for both standard and hard puzzles.
- `-d --decode` decodes the solution encodings from `minisat` into markdown tables and outputs them to `benchmarks/solutions`. Will output one solution for every solvable input puzzle.
- `-C --complete` same as combining `-a -k -d -S`.
- `-c --clean` deletes all files in the `benchmarks` directory and exits immediately.
- `-h --help` prints the help message.

### Output
While running, files generated by `sud2sat` and `minisat` will be stored in the `.working` directory. These will be deleted when the script finishes, unless the `-k` flag is specified, in which case they will be stored in the `benchmarks` directory.
All of the output files described below are stored under the `benchmarks` directory.
- When `-k` is specified, the `encodings` directory will contain CNF encodings for puzzles under `[encoding_type]/[test_type]/`; where `[encoding_type]` is either `minimum` or `efficient` or `extended`, and `[test_type]` is either `standard` or `hard`; and the solution encodings from `minisat` will be stored in `sat/[test_type]`. Solution encodings are not generated for each encoding type, as the encoding type does not affect the solution.
- When `-d` is specified, the `solutions` directory will contain the decoded solutions from `minisat`. When `-S` is specified, the `summary.md` file will contain the summary of the benchmarking results.
- When `-a` is specified, a file `[##]-[test_type]-[encoding_type].md` file will be created for each test type and encoding type, numbered in the order the tests were ran. These files will contain select output from `minisat` for each puzzle, and the summary of the benchmarking results for each test. The `summary.md` file will contain the summary of the benchmarking results for each encoding and test type when `-S` is specified. Additionally the `encodings` directory will contain `[encoding_type]/[test_type]/`, `sat/[test_type]` for each encoding and test type when `-k` is specified.
- If `-d` is specified, the decoded solutions for each test can be found in the `solutions/[test_type]` directory. Solutions are not generated for each encoding, as the encoding type does not affect the solution.
- If `-S` is specified, the `summary.md` file will contain the summary of the benchmarking results for each encoding and test type.
- When `-C` is specified, all the outputs from `-a -k -d -S` will be generated.

## Dependencies
- python3
- minisat2

## Sources
Puzzles in /data/puzzles taken from:

- https://projecteuler.net/project/resources/p096_sudoku.txt

- http://magictour.free.fr/top95
