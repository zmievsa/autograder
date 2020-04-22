# Installation (Linux-only) (Python >= 3.6)
* Run `pip3 install assignment-autograder`
* If you want to update to a newer version, run `pip3 install --upgrade --no-cache-dir assignment-autograder`
# Quickstart
* Currently, there is support for grading C, Java, and Python code
* Go to examples/ and look at simplest_c for the simplest usage scenario
* More complex scenarios are described below and in other directories in examples/
# Usage
1) Create tests directory in the same directory as student submissions. It has to follow the same structure as one of the examples.
2) Write testcases as described below. You can use examples/ as reference.
3) Create input and output text files in their respective directories for each testcase. If a test does not require input and/or output, the respective text file is also not required.
4) run `autograder path/to/submissions/dir` from command line. If you are in the same directory as submissions, you can simply run `autograder`.
## Advanced Usage
* You can use --generate_results (or -g) command line argument to generate a result file per student. It will have the same name as student's original submission.
* There are other command line arguments available. Simply run `autograder -h` to see them.
* If you create config.ini in tests, you can customize grader's behavior. You can use autograder/default_config.ini as a reference. If you don't add some configuration fields, grader will use the default fields from default config.
* You can specify filters as a comma separated list in config.ini. You can find filter function list in the autograder/filters.py. If you want to add your own filters, you will need to add them to autograder/filters.py
## Writing testcases
* Write a main that follows the same structure as the respective example. The main should usually call student's code and check its result (when working with output, you usually don't check the result, and simply allow grader to handle that)
* Assume that student's code is available in your namespace. Examples demonstrate exactly how to call students' functions.
* Assume that helper functions CHECK_OUTPUT(), RESULT(int r), PASS(), FAIL() are predefined and use them to return student scores to the grader
* Each helper function terminates the execution of the program and returns its respective exit code that signifies student's score for the testcase
* Each testcase is graded out of 100%, which means that you can fully control how much partial credit is given
* ### Helper functions
    * CHECK_OUTPUT() indicates that we do not check student's return values for the testcase and that we only care about their output (stdout).
    * RESULT(int r) returns student's score r back to the grader
    * PASS() returns the score of 100% back to the grader and is equivalent to RESULT(100)
    * FAIL() returns the score of 0% back to the grader and is equivalent to RESULT(0)
# Implementation details
* Exit codes  1 - 2, 126 - 165, and 255 have special meaning and should NOT be used for student scores. In the latest version of this readme, I used 0, 3-103 where 0 means CHECK_OUTPUT and 3-103 stand for respective student scores minus 3. The shift by 3 is used to prevent the use of standard exit codes
* If you want to add a new language for grading, you have to create a subclass of TestCase in autograder/testcases.py following the pattern of other subclasses and a respective test helper module in autograder/tests/test_helpers directory, then import the subclass into autograder/grader.py, and add it to ALLOWED_LANGUAGES dictionary
* At the point of writing this readme, output checking is a PASS or FAIL process (i.e. no partial credit possible). The reason is that allowing for 'partial similarity' of outputs is too error-prone and could yield too many points for students that did not actually complete the task properly. If you want to increase the chances of students' output matching, you should use FILTER_FUNCTION(s) defined in autograder/grader.py instead
* If you don't prototype student functions in your C testcases, you will run into undefined behavior. 
* Multiprocessing was a feature in the past but it has so many drawbacks that it was deemed unnecessary for the task
