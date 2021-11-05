Homework Test Results

TestCase                                Result
================================================================
test_output                             Failed to compile
/usr/bin/ld: .../student_with_wrong_assignment_name.o: in function `fibonacci':
student_with_wrong_assignment_name.c:(.text+0x29): undefined reference to `fib'
/usr/bin/ld: student_with_wrong_assignment_name.c:(.text+0x3d): undefined reference to `fib'
collect2: error: ld returned 1 exit status
test_result                             Failed to compile
/usr/bin/ld: .../student_with_wrong_assignment_name.o: in function `fibonacci':
student_with_wrong_assignment_name.c:(.text+0x29): undefined reference to `fib'
/usr/bin/ld: student_with_wrong_assignment_name.c:(.text+0x3d): undefined reference to `fib'
collect2: error: ld returned 1 exit status
test_time                               Failed to compile
/usr/bin/ld: .../student_with_wrong_assignment_name.o: in function `fibonacci':
student_with_wrong_assignment_name.c:(.text+0x29): undefined reference to `fib'
/usr/bin/ld: student_with_wrong_assignment_name.c:(.text+0x3d): undefined reference to `fib'
collect2: error: ld returned 1 exit status
================================================================
Result: 0/100

Key:
	Failed to Compile: Your submission did not compile due to a syntax or naming error
	Compiled with warnings: Your submission uses unchecked or unsafe operations
	Crashed due to signal SIGNAL_CODE: Your submission threw an uncaught exception.
	All signal error codes are described here: https://man7.org/linux/man-pages/man7/signal.7.html
	Exceeded Time Limit: Your submission took too much time to run (probably an infinite loop)
