#include <stdio.h>


unsigned long long fibonacci(int n) {
    unsigned long long a = 0, b = 1, c;
    unsigned int i;
    if (n == 0)
        return a;
    for (i = 2; i <= n; i++)
    {
        c = a + b;
        a = b;
        b = c;
    }
    printf("Result: %llu\n", b);
    return b;
}

void fibonacci_from_input() {
    unsigned long long n;
    scanf("%d", &n);
    fibonacci(n);
}


int main() {
    printf("%llu\n", fibonacci(6));
    printf("%llu\n", fibonacci(0));
    printf("%llu\n", fibonacci(2));
    printf("%llu\n", fibonacci(8));
    printf("%llu\n", fibonacci(24));

    return 0;
}
