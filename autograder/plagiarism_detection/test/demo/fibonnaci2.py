def fibonnaci(n):
    dp = [0, 1]
    for i in range(2, n + 1):
        dp.append(dp[i - 2] + dp[i - 1])
    return dp[n]
