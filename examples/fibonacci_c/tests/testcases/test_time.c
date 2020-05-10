unsigned long long fibonacci(int n);

int main() {
    unsigned long long r = fibonacci(46);
    if (r == 1836311903)
        PASS();
    else
        FAIL();
}