public class Fibonnaci4 {
    int n;

    public Fibonnaci4(int n) {
        this.n = fibonacci(n);
    }

    public int fibonacci(int n) {
        int[] dp = new int[2];
        dp[0] = 0;
        dp[1] = 1;
        for (int i = 2; i <= n; i++) {
            dp[i%2] += dp[(i+1)%2];
        }
        return dp[n];
    }
}