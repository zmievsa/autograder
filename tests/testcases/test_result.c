// This is a made up example of a test case that demonstrates the functionality of the grader

int main() {
    int res = numberSaver();
    if (res == 54)
        return PASS;        // Macro defined in testcase.py at compilation step
                            // Equivalent to RESULT(100)
    else if (res == 83)
        return RESULT(83);  // Sets student score for the testcase to 83%
    else
        return FAIL;        // Equivalent to RESULT(0)
}