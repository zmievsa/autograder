def fibonnaci(n):
    dp = [0 for i in range(max(2, n + 1))]
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 2] + dp[i - 1]
    return dp[n]
