from .clear_terminal import clear_terminal

def help():
    clear_terminal()
    print("Usage")
    print("--------------------")
    print("1. Setup")

    print("You can edit these values at any time in the `config.json` file in the Data folder")
    print("--------------------")
    print("2. Encoding")

    print("--------------------")
    print("3. Decoding")

    print()
    inp = input("Press Enter to go back: ")