public class Fibonnaci2 {
    int n;

    public Fibonnaci2(int n) {
        this.n = fibonacci(n);
    }

    public int fibonacci(int n) {
        if (n <= 0) return 0;
        if (n == 1) return 1;
        return fibonacci(n-2) + fibonacci(n-1);
    }
}