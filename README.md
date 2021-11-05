This utility aims to provide a simple, yet secure and highly configurable way to autograde programming assignments.

I consider it to be finished. Autograder has been tested on a real university class with hundreds of students and has shown to be error-less (in terms of grades), fast, and protected from cheating.
#### Table of Contents  
[Features](#Features) 
[Installation](#Platform-Support)  
[Installation](#Installation)   
[Supported Programming Languages](#Supported-Programming-Languages)   
[Quickstart](#Quickstart)   
[Usage](#Usage)   
[Writing testcases](#Writing-testcases)  
[Helper functions](#Helper-functions)  
[Limitations](#Limitations)   
[Anti Cheating](#Anti-Cheating)   
[Adding Programming Languages](#Adding-Programming-Languages)
# Features
* Most features are demonstrated in examples/ directory
* [Easy to grade](#Usage) 
* [Easy-to-write testcases](#Writing-testcases)  
* Testcase grade can be based on [student's stdout](#Helper-functions)
* Can grade C, C++, Java, and Python code
* A file with testcase results will be generated for each student
* You can customize the total points for the assignment, maximum running time of student's program, file names to be considered for grading, formatters for checking student stdout, and [much more](https://github.com/Ovsyanka83/autograder/blob/master/autograder/default_config.ini).
* [Anti Cheating capabilities](#Anti-Cheating) that make it nearly impossible for students to break the grader and choose their grades.
* Grading submissions in multiple programming languages at once, as long as there are testcases written in each language.
* Most of these features are described in detail in [default_config.ini](https://github.com/Ovsyanka83/autograder/blob/master/autograder/default_config.ini) and demonstrated in examples/ directory.
* Stdout-only (language-agnostic) grading supported
* JSON result output supported if autograder needs to be integrated as a part of a larger utility
# Platform Support
* Linux is fully supported
* OS X has not been tested
* Windows is partially supported:
  * C/C++ have only been tested with `mingw` installed with `chocolatey`
  * Java is only supported if autograder is run with Administrative privileges
  * Stdout-testcases that require compilation are only supported if `make` is installed
  * Stdout-testcases that require shebang lines are not supported
# Installation
* Currently Python >= 3.7 is necessary.
* Run `pip3 install assignment-autograder`
* If you want to update to a newer version, run `pip3 install --upgrade --no-cache-dir assignment-autograder`
# Supported Programming Languages
* Java (only through javac and java alias)
* C (only through gcc)
* C++ (only through g++)
* CPython (3.6-3.10)
* Any programming language if stdout-only grading is used
# Quickstart
* Run `autograder guide path/to/directory/you'd/like/to/grade`. The guide will create all of the necessary configurations and directories for grading and will explain how to grade.
* Read [Usage](#Usage) section
# Usage
1) Create tests directory in the same directory as student submissions. Its structure is shown in [examples](https://github.com/Ovsyanka83/autograder/tree/master/examples). (can be automatically created using [--guide](#Quickstart))
1) __Optional__ files that can be automatically created by [--guide](#Quickstart) CLI option and whose use is demostrated by [examples](https://github.com/Ovsyanka83/autograder/tree/master/examples):
    1) Input (stdin) and expected output (__stdout__) text files in their respective directories for each testcase. If a test does not require input and/or stdout, the respective text file is also not required.
    1) Create [config.ini](https://github.com/Ovsyanka83/autograder/blob/master/autograder/default_config.ini) and change configuration to fit your needs (If you do not include some fields, autograder will use the respective fields from default_config.ini)
    1) Create [stdout_formatters.py](https://github.com/Ovsyanka83/autograder/blob/master/autograder/default_stdout_formatters.py) and edit it to fit your needs. They will format student's stdout to allow you to give credit to students even if their stdout is not exactly the same as expected.
1) Write testcases as described [below](#Writing-testcases) using [examples](https://github.com/Ovsyanka83/autograder/tree/master/examples) as reference.
1) Run `autograder run path/to/submissions/dir` from command line.
## Writing testcases
* Write a main that follows the same structure as one of the examples in your programming language. The main should usually call student's code, check its result, and call one of the helper functions (when working with stdout, you don't check the result, and simply allow autograder to handle grading by calling CHECK_STDOUT())
* Assume that student's code is available in your namespace. Examples demonstrate exactly how to call students' functions.
* Assume that helper functions CHECK_STDOUT(), RESULT(int r), PASS(), FAIL() are predefined and use them to return student scores to the grader
* Each helper function prints the student's score, __validation string__, terminates the execution of the program and returns its respective exit code that signifies to autograder if the testcase ended in a result, cheating attempt, or if stdout checking is necessary.
* Each testcase is graded out of 100% and each grade is a 64bit double precision floating point number, which means that you can fully control how much partial credit is given in non-stdout checking tests.
### Helper functions
  * CHECK_STDOUT() indicates that we do not check student's return values for the testcase and that we only care about their output (__stdout__) that will be checked by the autograder automatically using student's stdout and the output files with the same name stem as the testcase. (beware: printing anything within your testcase will break this functionality)
  * RESULT(double r) returns student's score r back to the grader (0 - 100)
  * PASS() returns the score of 100% back to the grader and is equivalent to RESULT(100)
  * FAIL() returns the score of 0% back to the grader and is equivalent to RESULT(0)
## Limitations
* At the point of writing this readme, stdout checking is a PASS or FAIL process (i.e. no partial credit possible). The reason is that allowing for 'partial similarity' of outputs is too error-prone and could yield too many points for students that did not actually complete the task properly. If you want to increase the chances of students' stdout matching, you should use stdout formatters described [above](#Usage).
* If you don't prototype student functions you want to test in your C/C++ testcases, you will run into undefined behavior because of how C and C++ handle linking.
* __Student's main functions ARE NOT meant to be accessed because testcase must be the starting point of the program.__ They are, however, accessible if necessary but undocumented in general case and always accessible in stdout-only grading.
## Anti Cheating
One of the main weaknesses of automatic grading is how prone it is to cheating. Autograder tries to solve this problem with methods described in this section. Currently, (as far as I've read and tested), it is impossible to cheat autograder. However, Java might still have some weird ways of doing this but there are protections against all of the most popular scenarios (decompiling and parsing testcases, using System.exit, trying to read security key from environment variables, using reflection to use private members of the test helper)
* To restrict the student from exiting the process himself and printing the grade of his/her choice, I validate testcase stdout using a pseudorandom key called __validation string__. Autograder gives the string to the testcase as an environment variable which is erased right after the testcase saves it, and then it is automatically printed on the last line of stdout before the testcase exits. The autograder, then, pops it from stdout and verifies that it is the same string it sent. If it is not, the student will get the respective error message and a 0 on the testcase.
* To prevent students from simply importing the string from the testcase file, test helper files (described above) all have some way of disallowing imports. For C/C++, it is the static identifier, for Java, it is the private method modifiers and SecurityManager to protect against reflection, for python it is throwing an error if __name__ != "__main__". I assume that similar precautions can be implemented in almost any language added into autograder.
* Simply parsing validating string from the testcase file is impossible because it is passed at runtime.
* As an additional (and maybe unnecessary) security measure, autograder precompiles testcases without linking for all languages except for java, thus decreasing the possibility that the student will simply parse the testcase file and figure out the correct return values if the security measure above doesn't work.

# Adding Programming Languages
* If you want to add a new language for grading, you have to:
  1. Create a new directory in autograder/testcase_types/
  2. Create a python module in that directory that contains a subclass of TestCase (from autograder/testcase_utils/abstract_testcase.py)
  3. Create a helpers directory and write your test helper
  4. Optionally, add the extra (extra files to be available to each testcase) and templates (examples of testcases written using the new language) directories
* Use the other testcase subclasses and test helpers as reference
* This point is optional but if you want full anti-cheating capabilities for your new language, you will need to consider three things:
              
  * Does your language support getting and unsetting environment variables? It is required to save validating string in your code without leaking it to students.
  * Does your language support private-to-file functions/classes/methods/variables? It is required to prevent the student from simply importing helper functions and validating string.
  * Does your language support precompilation (conversion to bytecode without linking)? It is not as important as other points but could speed up grading and hide testcase code from students. 