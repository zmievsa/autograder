import sys, math
from antlr4 import InputStream, CommonTokenStream
from .lexers.Java8Lexer import JavaLexer
from .lexers.Python3Lexer import Python3Lexer

# entry point function that is called to compare a set of files with each other
def compare(files):
    numFiles = len(files)
    # add error handling
    if numFiles == 0:
        return "No files found"
    lexerClass, ignoreList, numTokens = initializeLanguage(files)
    # 2d array where [i][j] is the similarity score between the file at index i in files and the file at index j
    similarityScores = [[0 for x in range(numFiles)] for y in range(numFiles)]
    # get token stream for each file and total frequency for each token type
    tokenStreams, tokenFrequencies = parseFiles(files, lexerClass, ignoreList, numTokens)
    # construct similarity matrix to weight the significance of matching tokens. Matching uncommon tokens
    # is weighted heavier as it is more likely to be a result of plagiarism
    similarityMatrix = buildSimilarityMatrix(tokenFrequencies)
    # find the similarity score of comparing a file to itself. This is used to normalize the similarity score
    # calculated when comparing unique files
    self_similarities = buildSelfSimilarities(tokenStreams, similarityMatrix)
    # compare each file to every other file and return the resulting 2d array
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


# determine language of files and initialize language-specific variables
def initializeLanguage(files):
    prev = files[0].name.split(".")[1]
    # format: "file ending": [Lexer class used to parse, [ignore list of token types to ignore when parsing],
    # number of unique tokens in language]
    languageMapper = {
        "java": [JavaLexer, [-1, 106, 107], 105],
        "py": [Python3Lexer, [-1, 39], 97],
    }
    for i in range(len(files)):
        fileType = files[i].name.split(".")[1]
        if fileType != prev:
            return "File types don't match"
        prev = fileType

    return languageMapper[prev]


def parseFiles(files, lexerClass, ignoreList, numTokens):
    tokenStreams = []
    freq = [0 for x in range(numTokens + 1)]
    totalTokens = 0
    for i in range(len(files)):
        stream = InputStream(files[i].read())
        files[i].close()
        lexer = lexerClass(stream)
        tokens = CommonTokenStream(lexer)
        tokens.fetch(500)
        array = []
        for token in tokens.tokens:
            # remove comments, blank lines, etc
            if token.type not in ignoreList:
                array += [token.type]
                freq[token.type] += 1
                totalTokens += 1
        tokenStreams += [array]
    # find frequency of each token as percentage of total tokens
    for i in range(len(freq)):
        freq[i] = max(freq[i] / totalTokens, 1e-10)
    return tokenStreams, freq


def buildSimilarityMatrix(freq):
    # alpha is how heavily matching tokens should be penalized, beta is how heavily
    # mismatching tokens should be rewarded. alpha + beta = 1
    alpha = 0.65
    beta = 0.35
    matrixLen = len(freq) + 1
    matrix = [[0.0 for i in range(matrixLen)] for i in range(matrixLen)]
    for i in range(matrixLen):
        for j in range(i, matrixLen):
            # matching a gap with a gap is impossible
            if i == matrixLen - 1 and j == matrixLen - 1:
                value = -math.inf
            # value of matching token i with a gap
            elif j == matrixLen - 1:
                value = 4 * beta * math.log2(freq[i])
            # value of matching token i
            elif i == j:
                value = -1 * alpha * math.log2(freq[i] * freq[i])
            # value of matching two different tokens, i and j
            else:
                value = beta * math.log2(freq[i] * freq[j])
            # value of matching i and j is same as matching j and i
            matrix[i][j] = value
            matrix[j][i] = value
    return matrix


def buildSelfSimilarities(token_streams, matrix):
    self_similarities = []
    for i in range(len(token_streams)):
        tokens = token_streams[i]
        score = 0
        # for each token, find value of matching that token with itself and add to sum
        for tok in tokens:
            score += matrix[int(tok)][int(tok)]
        self_similarities.append(score)
    return self_similarities


def getSimilarity(a, b, matrix, self_similarity_sum):
    dp = [[0 for i in range(len(b))] for i in range(len(a))]
    # initialize dp with score of matching first token of each token stream
    dp[0][0] = max(0, matrix[a[0]][b[0]])
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
