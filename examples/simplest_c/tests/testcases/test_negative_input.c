// This is a made up example of a test case that demonstrates the functionality of the grader

int factorial(int n);

int main() {
    int answer = factorial(-83);
    if (answer == -1)
        PASS();
    else
        FAIL();
}