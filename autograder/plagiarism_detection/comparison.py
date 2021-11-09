import numpy as np
from numba import njit


@njit
def get_similarity(a: np.ndarray, b: np.ndarray, matrix: np.ndarray, self_similarity_sum: int) -> float:
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
