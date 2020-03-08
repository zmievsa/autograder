def NO_RESULT():
    exit(0)

def RESULT(result):
    exit(result + 3)

def PASS():
    RESULT(100)

def FAIL():
    RESULT(0)