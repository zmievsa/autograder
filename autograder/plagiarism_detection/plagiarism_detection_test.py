from plagiarism_detection import compare


def main():
    files = []
    f = open("test/java/CountPrimes1.java", "r")
    files += [f]
    f = open("test/java/CountPrimes2.java", "r")
    files += [f]
    f = open("test/java/CountPrimes3.java", "r")
    files += [f]
    f = open("test/java/CountPrimes4.java", "r")
    files += [f]

    # f = open("test/java/Test.java", "r")
    # files += [f]
    # f = open("test/java/Test2.java", "r")
    # files += [f]
    # f = open("test/java/Test3.java", "r")
    # files += [f]
    # for i in range(1):
    #     f = open("test/java/Test4.java", "r")
    #     files += [f]
    # files += [f]
    # for i in range(50):
    # 	f = open("test2.py", "r")
    # 	files += [f]
    print(compare(files))


if __name__ == "__main__":
    main()
