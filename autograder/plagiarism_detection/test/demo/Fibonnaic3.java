public class Fibonnaci3 {
    int n;

    public Fibonnaci3(int n) {
        this.n = fibonacci(n);
    }

    public int fibonacci(int n) {
        int[] dp = new int[Math.max(2, n+1)];
        dp[0] = 0;
        dp[1] = 1;
        for (int i = 2; i <= n; i++) {
            dp[i] = dp[i-2] + dp[i-1];
        }
        return dp[n];
    }
}