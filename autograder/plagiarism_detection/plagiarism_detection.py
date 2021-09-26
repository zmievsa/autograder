import sys, math
from antlr4 import *
from lexers.Java8Lexer import JavaLexer
from lexers.Python3Lexer import Python3Lexer


def compare(files):
    numFiles = len(files)
    # add error handling
    if numFiles == 0:
        return "No files found"
    lexerClass, ignoreList, numTokens = checkFileTypes(files)
    similarityScores = [[0 for x in range(numFiles)] for y in range(numFiles)]
    # get token stream for each file and total frequency for each token type
    tokenStreams, tokenFrequencies = parseFiles(
        files, lexerClass, ignoreList, numTokens
    )
    similarityMatrix = buildSimilarityMatrix(tokenFrequencies)
    self_similarities = buildSelfSimilarities(tokenStreams, similarityMatrix)
    for i in range(numFiles):
        for j in range(i + 1, numFiles):
            similarity = getSimilarity(
                tokenStreams[i],
                tokenStreams[j],
                similarityMatrix,
                self_similarities[i] + self_similarities[j],
            )
            similarityScores[i][j] = similarity
            similarityScores[j][i] = similarity
    return similarityScores


# lexerClass is the lexer to be used, ignoreList is a list containing the
# token types to remove when parsing, numTokens is the number of token types in the language
def checkFileTypes(files):
    prev = files[0].name.split(".")[1]
    for i in range(len(files)):
        fileType = files[i].name.split(".")[1]
        if fileType != prev:
            return "File types don't match"
        prev = fileType
        if fileType == "java":
            lexerClass = JavaLexer
            # ignore comments
            ignoreList = [-1, 106, 107]
            numTokens = 105
        elif fileType == "py":
            lexerClass = Python3Lexer
            # ignore comments and new lines
            ignoreList = [-1, 39]
            numTokens = 97
    return lexerClass, ignoreList, numTokens


def parseFiles(files, lexerClass, ignoreList, numTokens):
    tokenStreams = []
    for i in range(len(files)):
        stream = InputStream(files[i].read())
        files[i].close()
        lexer = lexerClass(stream)
        tokens = CommonTokenStream(lexer)
        tokens.fetch(500)
        array = []
        freq = [0 for x in range(numTokens + 1)]
        totalTokens = 0
        for token in tokens.tokens:
            # remove comments
            if token.type not in ignoreList:
                array += [token.type]
                freq[token.type] += 1
                totalTokens += 1
        tokenStreams += [array]
        for i in range(len(freq)):
            freq[i] = max(freq[i] / totalTokens, 0.0000000001)
    return tokenStreams, freq


def buildSimilarityMatrix(freq):
    alpha = 0.65
    beta = 0.35
    matrixLen = len(freq) + 1
    matrix = [[0.0 for i in range(matrixLen)] for i in range(matrixLen)]
    for i in range(matrixLen):
        for j in range(i, matrixLen):
            if i == matrixLen - 1 and j == matrixLen - 1:
                value = -math.inf
            elif i == matrixLen - 1:
                value = 4 * beta * math.log2(freq[j])
            elif j == matrixLen - 1:
                value = 4 * beta * math.log2(freq[i])
            elif i == j:
                value = -1 * alpha * math.log2(freq[i] * freq[i])
            else:
                value = beta * math.log2(freq[i] * freq[j])
            matrix[i][j] = value
            matrix[j][i] = value
    return matrix


def buildSelfSimilarities(token_streams, matrix):
    # print(matrix)
    self_similarities = []
    for i in range(len(token_streams)):
        tokens = token_streams[i]
        score = 0
        for tok in tokens:
            score += matrix[int(tok)][int(tok)]
        self_similarities.append(score)
    return self_similarities


def getSimilarity(a, b, matrix, self_similarity_sum):
    dp = [[0 for i in range(len(b))] for i in range(len(a))]
    dp[0][0] = matrix[a[0]][b[0]]
    for i in range(len(a)):
        for j in range(len(b)):
            maxScore = 0
            # score from matching both tokens
            if i != 0 and j != 0:
                maxScore = max(maxScore, dp[i - 1][j - 1] + matrix[a[i]][b[j]])
            # score from matching i token with gap
            if i != 0:
                maxScore = max(maxScore, dp[i - 1][j] + matrix[a[i]][-1])
            # score from matching j token with gap
            if j != 0:
                maxScore = max(maxScore, dp[i][j - 1] + matrix[-1][b[j]])
            # print("" + str(i) + ", " + str(j) + "\n")
            dp[i][j] = max(maxScore, dp[i][j])
    return dp[-1][-1] * 2 / self_similarity_sum
