unsigned long long fibonacci(int n);

int main() {
    unsigned long long r1, r2, r3, r4;
    r1 = fibonacci(0);
    r2 = fibonacci(2);
    r3 = fibonacci(8);
    r4 = fibonacci(24);
    int score = 0;
    if (r1 == 0)     score += 25;
    if (r2 == 1)     score += 25;
    if (r3 == 21)    score += 25;
    if (r4 == 46368) score += 25;
    RESULT(score);
}
