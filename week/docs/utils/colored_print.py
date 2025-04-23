RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
LIGHTBLUE = "\033[94m"
RESET = "\033[0m"

def print_red(string):
    print(f"{RED}{string}{RESET}")

def print_yellow(string):
    print(f"{YELLOW}{string}{RESET}")

def print_green(string):
    print(f"{GREEN}{string}{RESET}")

def print_blue(string):
    print(f"{BLUE}{string}{RESET}")

def print_lblue(string):
    print(f"{LIGHTBLUE}{string}{RESET}")
