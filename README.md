This utility aims to provide a simple, yet secure and highly configurable way to autograde programming assignments.

I consider it to be finished. From now on, I will only be adding extra grading languages if necessary and fixing bugs if any are reported. Autograder has been tested on a real university class with hundreds of students and has shown to be error-less (in terms of grades), almost completely safe from cheating, and fast.
#### Table of Contents  
[Features](#Features)   
[Installation](#Installation)   
[Quickstart](#Quickstart)   
[Supported Programming Languages](#Supported-Programming-Languages)   
[Usage](#Usage)   
[Advanced Usage](#Advanced-Usage)   
[Writing testcases](#Writing-testcases)  
[Helper functions](#Helper-functions)  
[Command line help](#Command-line-help)  
[Implementation details](#Implementation-details)  
[Anti Cheating](#Anti-Cheating)   
[Adding Programming Languages](#Adding-Programming-Languages)
# Features
* Most features are demonstrated in examples/ directory
* Easy to grade (simply running `autograder` on a directory with assignments and testcases)
* Easy-to-write testcases
* Testcase grade can be based on student's output in stdout
* A per-testcase grade can be any number out of 100 points
* Support for grading C, C++, Java, and Python code
* A file with testcase results can be generated for each student (done by default)
* You can customize the total points for the assignment, timeout for the running time of student's program, file names to be considered for grading, and filters for checking student output
* Anti-Cheating capabilities that make it nearly impossible for students to break the grader and choose their results (precompilation of testcases, verification of who exited the program, and removal of testcase source files before testing). You can read more on this in implementation details section below
* You can pass arguments to language compilers during testcase (or submission) precompilation and compilation using config.ini
* You can grade submissions in multiple programming languages at once, as long as there are testcases written in each language
* Most of these features are described in detail in autograder/default_config.ini, implementation details section below, and command line help section below
# Installation
* Currently, Linux-only and Python >= 3.6. OS X has not been tested. Windows, Python < 3.6 are not supported at all.
* Run `pip3 install assignment-autograder`
* If you want to update to a newer version, run `pip3 install --upgrade --no-cache-dir assignment-autograder`
# Quickstart
* Run `autograder path/to/directory/you'd/like/to/grade --guide`. The guide will create all of the necessary configurations and directories for grading and will explain how to grade.
# Supported Programming Languages
* Java (only through javac and java alias)
* C (only through gcc)
* C++ (only through g++)
* CPython (3.6-3.10)
# Usage
1) Create tests directory in the same directory as student submissions. It has to follow the same structure as one of the examples. (can be automatically created using instructions from quickstart section)
2) Write testcases as described below. You can use examples/ as reference.
3) Create input and output text files in their respective directories for each testcase. If a test does not require input and/or output, the respective text file is also not required.
4) run `autograder path/to/submissions/dir` from command line. If you are in the same directory as submissions, you can simply run `autograder`.
## Advanced Usage
* If you create config.ini in tests, you can customize grader's behavior. Use `autograder --guide` if you want all optional directories and configurations set up for you. If you remove some configuration fields from config.ini, grader will use the respective fields from default config.
* To check output, you can specify output formatters in a file output_formatters.py in the directory with your testcase folder. They will format student's output to allow you to give credit to students even if their output is not exactly the same as expected. To see how to write this file, you can look at autograder/default_formatters.py
## Writing testcases
* Write a main that follows the same structure as one of the examples in your programming language. The main should usually call student's code, check its result, and call one of the helper functions (when working with output, you don't check the result, and simply allow autograder to handle grading by calling CHECK_OUTPUT())
* Assume that student's code is available in your namespace. Examples demonstrate exactly how to call students' functions.
* Assume that helper functions CHECK_OUTPUT(), RESULT(int r), PASS(), FAIL() are predefined and use them to return student scores to the grader
* Each helper function terminates the execution of the program and returns its respective exit code that signifies student's score for the testcase
* Each testcase is graded out of 100% and allows you to specify grades down to a single percent, which means that you can fully control how much partial credit is given
### Helper functions
  * CHECK_OUTPUT() indicates that we do not check student's return values for the testcase and that we only care about their output (stdout) that will be checked by the autograder automatically using student's stdout and the output files with the same name stem as the testcase. (beware: printing anything within your testcase will break this functionality)
  * RESULT(int r) returns student's score r back to the grader (0 - 100)
  * PASS() returns the score of 100% back to the grader and is equivalent to RESULT(100)
  * FAIL() returns the score of 0% back to the grader and is equivalent to RESULT(0)
# Command line help
```
usage: autograder [-h] [-v] [-p [min_score]] [--no_output] [-s [<name> [<name> ...]]] [-g] [submission_path]

positional arguments:
  submission_path       Path to directory that contains student submissions

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show the version number
  -p [min_score], --print [min_score]
                        Use after already graded to print assignments with score >= min_score
  --no_output           Do not output any code to the console
  -s [<name> [<name> ...]], --submissions [<name> [<name> ...]]
                        Only grade submissions with specified file names (without full path)
  -g, --guide           Guide you through setting up a grading environment
```
# Implementation details
* I used exit codes to specify student grades. Currently, I choose an integer offset, add it to the student grade when returning from testcase, and subtract it when grading. This allows us to specify student scores using exit codes; CHECK_OUTPUT has its own exit code. The exit code range I use is carefully picked so that it does not use any exit codes occupied by the system. Even though this method seems prone to cheating at first, we mitigate that by the methods described in the anti cheating section.
* At the point of writing this readme, output checking is a PASS or FAIL process (i.e. no partial credit possible). The reason is that allowing for 'partial similarity' of outputs is too error-prone and could yield too many points for students that did not actually complete the task properly. If you want to increase the chances of students' output matching, you should use filter function(s) described in advanced usage section.
* If you don't prototype student functions you want to test in your C/C++ testcases, you will run into undefined behavior because of how c handles linking.

## Anti Cheating
One of the main weaknesses of automatic grading is how prone it is to cheating. Autograder tries to solve this problem with methods described in this section. Currently, it is impossible to cheat autograder in Python, C, C++ (as far as I've read and tested).

It is very unlikely that the student will be able to cheat autograder when using Java because it would require him to read and understand the source code of the grader and make private methods public in the testcase file (technically still possible but not easy at all), or get the validating string from the testcase class (I have made sure that this is impossible but I doubt any solution can be bullet-proof if the student has a lot of time and great Java experience). If the student is able to do all of these steps, he/she can easily pass most of bachelor-level courses where autograder can be applied without attempting to cheat. However, the possibility of cheating in Java is still nonzero which is why I am planning to try to implement protections against making private methods public. The description of anti-cheating features can be found below.
* To restrict the student from exiting the process himself and returning an exit code with the grade of his/her choice, I validate test output using a pseudorandom key called __validation string__. Autograder gives the string to the testcase as an environment variable which is erased right after the testcase saves it, and then it is automatically printed on the last line of stdout before the testcase exits. The autograder, then, pops it from stdout and verifies that it is the same string it sent. If it is not, the student will get the respective error message and a 0 on the testcase.
* To prevent students from simply importing the string from the testcase file, test helper files (described above) all have some way of disallowing imports. For C/C++, it is the static identifier, for Java, it is the private method modifiers, for python it is throwing an error if __name__ != "__main__". I assume that similar precautions can be implemented in almost any language added into autograder.
* Simply parsing validating string from the testcase file is impossible because it is saved at runtime.
* As an additional (and maybe unnecessary) security measure, autograder precompiles testcases without linking for all languages except for java, thus decreasing the possibility that the student will simply parse the testcase file and figure out the correct return values if the security measure above doesn't work.

# Adding Programming Languages
* If you want to add a new language for grading, you have to:
  1. create a new module with subclass of TestCase in autograder/testcases/
  2. add it into ALLOWED_LANGUAGES dictionary in autograder/testcases/\_\_init\_\_.py
  3. write a respective test helper module in autograder/testcases/test_helpers directory.
* Use the other testcase subclasses and test helpers as reference
* This point is optional but if you want full anti-cheating capabilities for your new language, you will need to consider three things:
              
  * Does your language support getting and unsetting environment variables? It is required to save validating string in your code without leaking it to students.
  * Does your language support private-to-file functions/classes/methods/variables? It is required to prevent the student from simply importing helper functions and validating string.
  * Does your language support precompilation (conversion to bytecode without linking)? It is not as important as other points but could speed up grading and hide testcase code from students. 