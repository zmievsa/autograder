int main() {
    int res = numberSaver();
    if (res == 54)
        return PASS; // Macro defined in grader.py at compilation step
                     // Equivalent to RESULT(100)
    else
        return FAIL; // Equivalent to RESULT(0)
    // If you wanted to give some score except 0 and 100, you'd use 'return RESULT(whatever_your_testcase_score_is)'
}