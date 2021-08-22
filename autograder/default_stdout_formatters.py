# These functions will format both the expected and student's outputs to compare them against each other
# It is not required to specify any outputs for your testcase_utils. I.e. If you want, you do not even have to create
# stdout_formatters.py in your directory or you can leave it blank. Type hints are also not required and are only
# here for reference.

# For specific (not ALL) formatters, you name them after their testcase files. I.e. If testcase file has a name
# "TestFactorial.java", the formatter's name will be TestFactorial(s: str)
# (function argument name can be anything and is unimportant).


# def ALL(s: str) -> str:
#     """This is a default formatter that will be used on all testcase
#     outputs by default if no other formatters are specified for them

#     This formatter will only leave digits in the output because the author
#     of it decided that any other text is unimportant for the purposes of his testing.
#     """
#     return "".join(filter(lambda c: c.isdigit(), s))


# def testcase1(s: str) -> str:
#     """Only this formatter will be applied to testcase1
#     It will remove all digits from output.
#     """
#     return "".join(filter(lambda c: not c.isdigit(), s))


# def testcase2(s: str) -> str:
#     """Only this formatter will be applied to testcase2
#     It will remove all spaces from output.
#     """
#     return s.replace(" ", "")


# def testcase3(s: str) -> str:
#     """Only this formatter will be applied to testcase3
#     It will remove all whitespace from output.
#     """
#     return "".join(filter(lambda c: not c.isspace(), s))
