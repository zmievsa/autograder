import sys, math, pathlib
import numpy as np
from antlr4 import *
from lexers.Java8Lexer import JavaLexer
from lexers.Python3Lexer import Python3Lexer
from lexers.CLexer import CLexer
from lexers.CppLexer import CppLexer
from comparison import getSimilarity

# entry point function that is called to compare a set of files with each other
def compare(paths):
    numFiles = len(paths)
    # add error handling
    if numFiles == 0:
        raise ValueError("No files found")
    language_map = initializeLanguage(paths)
    results = {}
    similarity_scores = {}
    for language in language_map:
        files = language_map[language]["files"]
        # get token stream for each file and total frequency for each token type
        parsed_file_map = parseFiles(language_map[language])
        # construct similarity matrix to weight the significance of matching tokens. Matching uncommon tokens
        # is weighted heavier as it is more likely to be a result of plagiarism
        similarityMatrix = buildSimilarityMatrix(parsed_file_map["freq"])
        # find the similarity score of comparing a file to itself. This is used to normalize the similarity score
        # calculated when comparing unique files
        self_similarities = buildSelfSimilarities(
            parsed_file_map["token_streams"], similarityMatrix
        )
        token_streams = parsed_file_map["token_streams"]
        # compare each file to every other file and return the resulting 2d array
        for i in range(len(token_streams)):
            for j in range(i + 1, len(token_streams)):
                similarity = getSimilarity(
                    token_streams[i],
                    token_streams[j],
                    similarityMatrix,
                    self_similarities[i] + self_similarities[j],
                )
                similarity_scores[frozenset((files[i], files[j]))] = similarity
        results[language] = similarity_scores
    return similarity_scores


# determine language of files and initialize language-specific variables
def initializeLanguage(paths):
    language_partition = {"java": [], "py": [], "c": [], "cpp": []}

    for path in paths:
        language_partition[path.suffix.split(".")[-1]].append(path)

    # format: "file ending": [Lexer class used to parse, [ignore list of token types to ignore when parsing],
    # number of unique tokens in language]
    language_mapper = {
        "java": {"lexer": JavaLexer, "ignore_list": [-1, 106, 107], "num_tokens": 105},
        "py": {"lexer": Python3Lexer, "ignore_list": [-1, 39], "num_tokens": 97},
        "c": {"lexer": CLexer, "ignore_list": [-1, 117, 118], "num_tokens": 119},
        "cpp": {"lexer": CppLexer, "ignore_list": [-1, 144, 145], "num_tokens": 146},
    }
    # add files of each programming language to mapper object
    for key in language_mapper:
        language_mapper[key]["files"] = language_partition[key]
    return language_mapper


def parseFiles(language):
    files = language["files"]
    lexer_class = language["lexer"]
    ignore_list = language["ignore_list"]
    tokenStreams = []
    freq = [0 for x in range(language["num_tokens"] + 1)]
    totalTokens = 0
    for file in files:
        with file.open() as f:
            stream = InputStream(f.read())
            lexer = lexer_class(stream)
            tokens = CommonTokenStream(lexer)
            # TODO: look at fetch
            tokens.fetch(5000)
            array = []
            for token in tokens.tokens:
                # remove comments, blank lines, etc
                if token.type not in ignore_list:
                    array += [token.type]
                    freq[token.type] += 1
                    totalTokens += 1
            tokenStreams += [array]
    # find frequency of each token as percentage of total tokens
    if totalTokens == 0:
        freq = [1e-10 for x in range(len(freq))]
    else:
        for i in range(len(freq)):
            freq[i] = max(freq[i] / totalTokens, 1e-10)
    return {"token_streams": tokenStreams, "freq": freq}


def buildSimilarityMatrix(freq):
    # alpha is how heavily matching tokens should be penalized, beta is how heavily
    # mismatching tokens should be rewarded. alpha + beta = 1
    alpha = 0.65
    beta = 0.35
    matrixLen = len(freq) + 1
    matrix = [[0 for i in range(matrixLen)] for i in range(matrixLen)]
    for i in range(matrixLen):
        for j in range(i, matrixLen):
            # matching a gap with a gap is impossible
            if i == matrixLen - 1 and j == matrixLen - 1:
                value = 1e10
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
            matrix[i][j] = int(1000 * value)
            matrix[j][i] = int(1000 * value)
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
