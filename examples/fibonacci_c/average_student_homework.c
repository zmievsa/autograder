#include <stdio.h>


unsigned long long fibonacci_inner(unsigned long long n) {
   if (n <= 1)
      return n;
   return fibonacci_inner(n-1) + fibonacci_inner(n-2);
}

unsigned long long fibonacci(unsigned long long n) {
    unsigned long long result = fibonacci_inner(n);
    printf("Fibonacci(n) = %llu\n", result);
    return result;
}

void fibonacci_from_input() {
    unsigned long long n;
    scanf("%d", &n);
    fibonacci(n);
}

int main() {
    fibonacci(45);
}