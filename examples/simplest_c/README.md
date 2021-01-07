* This example shows the the simplest directory structure possible with autograder and clarifies the main features:
* Input and output directories and files are optional.
  * If your testcase does not use input or check stdout, you don't need to make input and output files for it.
  * If none of your testcases use input and/or output, you can completely omit the respective directories.
* config.ini can be omitted because the grader will use the default values instead. It will also guess the programming language from your testcase suffixes
* testcases and submissions don't have to follow any naming convention. But it is recommended that you use snake case for testcase names for prettier output
