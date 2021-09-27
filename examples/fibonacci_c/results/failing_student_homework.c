Homework Test Results

================================================================
Failed to precompile:
/ovsyanka/code/autograder/examples/fibonacci_c/temp/failing_student_homework.c/failing_student_homework.c: In function ‘fibonacci’:
.../failing_student_homework.c:2:15: error: ‘P’ undeclared (first use in this function)
    2 |    if (n <= 1)P
      |               ^
.../failing_student_homework.c:2:15: note: each undeclared identifier is reported only once for each function it appears in
.../failing_student_homework.c:2:16: error: expected ‘;’ before ‘return’
    2 |    if (n <= 1)P
      |                ^
      |                ;
    3 |       return n;
      |       ~~~~~~    
.../failing_student_homework.c:4:11: warning: implicit declaration of function ‘fib’ [-Wimplicit-function-declaration]
    4 |    return fib(n-1) + fib(n-2);
      |           ^~~
================================================================
Result: 0/100

Key:
	Failed to Compile: Your submission did not compile due to a syntax or naming error
	Compiled with warnings: Your submission uses unchecked or unsafe operations
	Crashed due to signal SIGNAL_CODE: Your submission threw an uncaught exception.
	All signal error codes are described here: https://man7.org/linux/man-pages/man7/signal.7.html
	Exceeded Time Limit: Your submission took too much time to run (probably an infinite loop)
