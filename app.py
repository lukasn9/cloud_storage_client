import sys

from Data.scripts.encoding import encode
from Data.scripts.decoding import decode
from Data.scripts.clear_terminal import clear_terminal
from Data.scripts.help import help

def main():
    while True:
        clear_terminal()
        inp = str(input("Encode/Decode/Help (1/2/3/Exit): "))

        if int(inp) == 1:
            encode()
        elif int(inp) == 2:
            decode()
        elif int(inp) == 3:
            help()
        else:
            sys.exit(0)

if __name__ == "__main__":
    clear_terminal()
    main()