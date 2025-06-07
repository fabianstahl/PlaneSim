def parse_list(string, dtype):
    return [dtype(x) for x in string.split(",")]