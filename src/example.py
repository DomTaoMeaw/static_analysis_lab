def calc(a, b):
    x = 0
    if a > 0:
        if b > 0:
            if a > b:
                x = a - b
            else:
                x = b - a
    return x
