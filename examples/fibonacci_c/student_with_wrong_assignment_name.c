int fibonacci(int n) {
   if (n <= 1)
      return n;
   return fib(n-2) + fib(n-2);
}