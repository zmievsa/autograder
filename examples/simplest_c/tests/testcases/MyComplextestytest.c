// This is a made up example of a test case that demonstrates
// the functionality of the grader.
// To be honest, this testcase alone is enough to calculate
// student score but it is recommended that you split complex
// testcases into simpler ones for better output and more partial
// credit.

int factorial(int n);

int main() {
    int inputs[] = {-1, 0, 1, 2, 3, 4, 5, 6, 7, 8};
    int factorials[] = {-1, 1, 1, 2, 6, 24, 120, 720, 5040, 40320};
    int result = 0;
    for (int i = 0; i < 10; i++) {
        if (factorial(inputs[i]) == factorials[i])
            result += 10;
    }
    RESULT(result);
}