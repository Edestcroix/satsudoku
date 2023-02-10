import fileinput
import sys

from . import encode


def main():
    # get the sudoku from stdin
    try:
        sudoku = "".join(list(fileinput.input()))
    except FileNotFoundError:
        # get from arguments if no input is given
        sudoku = " ".join(sys.argv[1:])

    print(encode(sudoku))


if __name__ == "__main__":
    main()
