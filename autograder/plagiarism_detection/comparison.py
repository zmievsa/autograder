from numba import jit
import numpy as np

# average 9.1 seconds
def getSimilarity(a, b, matrix, self_similarity_sum):
    # dp = np.zeros((len(a), len(b)), dtype=int)
    dp = [[0 for i in range(len(b))] for i in range(len(a))]
    # initialize dp with score of matching first token of each token stream
    dp[0, 0] = max(0, matrix[a[0], b[0]])
    for i in range(1, len(a)):
        dp[0, i] = max(0, dp[0, i - 1] + matrix[-1, b[i]])
        dp[i, 0] = max(0, dp[i - 1, 0] + matrix[a[i], -1])
    for i in range(1, len(a)):
        for j in range(1, len(b)):
            # # score from matching both tokens
            maxScore = max(
                0,
                dp[i - 1, j - 1] + matrix[a[i], b[j]],
                dp[i - 1, j] + matrix[a[i], -1],
                dp[i, j - 1] + matrix[-1, b[j]],
                dp[i, j],
            )
            dp[i][j] = maxScore
    return dp[-1, -1] * 2 / self_similarity_sum


@jit(nopython=True)
def getSimilarity2(a, b, matrix, self_similarity_sum):
    dp = np.zeros((len(a), len(b)), dtype=np.int32)
    # initialize dp with score of matching first token of each token stream
    dp[0, 0] = max(0, matrix[a[0], b[0]])
    for i in range(1, len(a)):
        dp[i, 0] = max(0, dp[i - 1, 0] + matrix[a[i], -1])
    for i in range(1, len(b)):
        dp[0, i] = max(0, dp[0, i - 1] + matrix[-1, b[i]])
    for i in range(1, len(a)):
        for j in range(1, len(b)):
            # # score from matching both tokens
            maxScore = max(
                (
                    0,
                    dp[i - 1, j - 1] + matrix[a[i], b[j]],
                    dp[i - 1, j] + matrix[a[i], -1],
                    dp[i, j - 1] + matrix[-1, b[j]],
                )
            )
            dp[i, j] = maxScore
    return dp[-1, -1] * 2 / self_similarity_sum
