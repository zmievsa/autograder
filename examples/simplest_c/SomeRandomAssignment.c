#include <stdio.h>

int factorial(int n)
{
    if (n < 0)
        return -1;
    int fact = 1;
    for (int i = 2; i <= n; i++)
        fact *= i;
    return fact;

}

int main() {
    int n;
    scanf("Please, input your number: %d", &n);
    printf("%d! = %d", factorial(n));
    return 0;
}
