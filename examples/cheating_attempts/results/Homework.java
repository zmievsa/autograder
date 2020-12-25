Homework Test Results

TestCase                                Result
================================================================
Testenv                                 Crashed due to signal 1:
Exception in thread "main" java.lang.SecurityException: Using environ is not permitted. It could indicate cheating.
	at NoReflectionAndEnvVarsSecurityManager.checkPermission(NoReflectionAndEnvVarsSecurityManager.java:25)
	at java.lang.System.getenv(System.java:896)
	at Homework.test_env(Homework.java:5)
	at TestEnv.main(TestEnv.java:59)


Testexit                                None of the helper functions have been called.
Instead, exit() has been called with exit_code 103.
It could indicate student cheating or testcases being written incorrectly.
Testreflection                          Crashed due to signal 1:
Exception in thread "main" java.lang.SecurityException: Using reflection is not permitted. It could indicate cheating.
	at NoReflectionAndEnvVarsSecurityManager.checkPermission(NoReflectionAndEnvVarsSecurityManager.java:28)
	at java.lang.reflect.AccessibleObject.setAccessible(AccessibleObject.java:128)
	at Homework.test_reflection(Homework.java:14)
	at TestReflection.main(TestReflection.java:59)


================================================================
Result: 0/100

Key:
	Failed to Compile: Your submission did not compile due to a syntax or naming error
	Compiled with warnings: Your submission uses unchecked or unsafe operations
	Crashed due to signal SIGNAL_CODE: Your submission threw an uncaught exception.
	All signal error codes are described here: http://man7.org/linux/man-pages/man7/signal.7.html
	Exceeded Time Limit: Your submission took too much time to run (probably an infinite loop)
