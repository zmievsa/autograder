# Installation
1) Run `python setup.py install`
# Configuration
* Create testcases in tests/testcases
* Create their respective inputs and outputs in tests/input and tests/output
* Change configuration at the top of grader.py
* Put student submissions into submissions directory
## Writing testcases
* When writing testcases, assume that NO_RESULT(), RESULT(int r), PASS(), FAIL() functions are already predefined and use them to return student scores to the grader
* Each helper function terminates the execution of the program and returns its respective exit code that signifies student's score for the testcase
* Each testcase is graded out of 100%, which means that you can fully control how much partial credit is given
* ### Helper functions
    * NO_RESULT() indicates that we do not check student's return values for the testcase and that we only care about their output.
    * RESULT(int r) returns student's score r back to the grader
    * PASS() returns the score of 100% back to the grader and is equivalent to RESULT(100)
    * FAIL() returns the score of 0% back to the grader and is equivalent to RESULT(0)
    * Note: when grading java code, we don't use helper functions directly. Instead, we call them from TestHelper class which, you can assume, is predefined for your testcases
# Implementation details
* Exit codes  1 - 2, 126 - 165, and 255 have special meaning and should NOT be used for student scores. In the latest version of this readme, I used 0, 3-103 where 0 means NO_RESULT and 3-103 stand for respective student scores minus 3. The shift by 3 is used to prevent the use of standard exit codes
* If you want to add a new language for grading, you have to create a subclass of TestCase in testcases.py following the pattern of other subclasses and a respective test helper module in tests/test_helpers directory, then import the subclass into grader.py
* At the point of writing this readme, output checking is a PASS or FAIL process (i.e. no partial credit possible). The reason is that allowing for 'partial similarity' of outputs is too error-prone and could yield too much points for students that did not actually complete the task properly. If you want to increase the chances of students' output matching, you should use FILTER_FUNCTION(s) defined in grader.py instead
* If you don't prototype student functions in your C testcases, you will run into undefined behavior. 
