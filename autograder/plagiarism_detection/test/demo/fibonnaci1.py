def fibonnaci(n):
    if n <= 0:
        return 0
    if n == 1:
        return 1
    return fibonnaci(n - 2) + fibonnaci(n - 1)
