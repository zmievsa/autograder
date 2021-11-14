import math
from pathlib import Path
from typing import List

import numpy as np
from antlr4 import *

from .comparison import get_similarity
from .lexers.CLexer import CLexer
from .lexers.CppLexer import CppLexer
from .lexers.Java8Lexer import JavaLexer
from .lexers.Python3Lexer import Python3Lexer


# entry point function that is called to compare a set of files with each other
def compare(paths: List[Path]) -> dict:
    numFiles = len(paths)
    if numFiles == 0:
        raise ValueError("No files found")
    language_map = initialize_language(paths)
    results = {}
    for language in language_map:
        files = language_map[language]["files"]
        if len(files) == 0:
            continue
        # get token stream for each file and total frequency for each token type
        parsed_file_map = parse_files(language_map[language])
        token_streams = parsed_file_map["token_streams"]
        lengths = parsed_file_map["lengths"]
        # construct similarity matrix to weight the significance of matching tokens. Matching uncommon tokens
        # is weighted heavier as it is more likely to be a result of plagiarism
        similarityMatrix = build_similarity_matrix(parsed_file_map["freq"])
        # find the similarity score of comparing a file to itself. This is used to normalize the similarity score
        # calculated when comparing unique files
        self_similarities = build_self_similarities(token_streams, similarityMatrix, lengths)
        result = run_comparisons(token_streams, similarityMatrix, self_similarities, lengths)
        results[language] = convert_results(result, files)

    return results


# determine language of files and initialize language-specific variables
def initialize_language(paths: List[Path]) -> dict:
    language_partition = {"java": [], "py": [], "c": [], "cpp": []}

    for path in paths:
        language_partition[path.suffix.split(".")[-1]].append(path)

    # format: "file ending": [Lexer class used to parse, [ignore list of token types to ignore when parsing],
    # number of unique tokens in language]
    language_mapper = {
        "java": {
            "lexer": JavaLexer,
            "ignore_list": np.array([-1, 106, 107]),
            "num_tokens": 108,
        },
        "py": {
            "lexer": Python3Lexer,
            "ignore_list": np.array([-1, 39]),
            "num_tokens": 99,
        },
        "c": {
            "lexer": CLexer,
            "ignore_list": np.array([-1, 117, 118]),
            "num_tokens": 119,
        },
        "cpp": {
            "lexer": CppLexer,
            "ignore_list": np.array([-1, 144, 145]),
            "num_tokens": 146,
        },
    }
    # add files of each programming language to mapper object
    for key in language_mapper:
        language_mapper[key]["files"] = language_partition[key]
    return language_mapper


def parse_files(language: dict) -> dict:
    files = language["files"]
    lexer_class = language["lexer"]
    ignore_list = language["ignore_list"]
    num_tokens = language["num_tokens"]
    tokenStreams = []
    freq = [0 for x in range(num_tokens + 1)]
    total_tokens = 0
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
                if token.type > num_tokens:
                    pass
                if token.type not in ignore_list and token.type <= num_tokens:
                    array += [token.type]
                    freq[token.type] += 1
                    total_tokens += 1
            tokenStreams += [np.array(array)]
    # find frequency of each token as percentage of total tokens
    if total_tokens == 0:
        freq = [1e-10 for x in range(len(freq))]
    else:
        for i in range(len(freq)):
            freq[i] = max(freq[i] / total_tokens, 1e-10)
    lengths = np.array([len(x) for x in tokenStreams])
    converted_token_stream = np.zeros((len(tokenStreams), np.max(lengths)), np.int32)
    for i in range(len(tokenStreams)):
        converted_token_stream[i, : lengths[i]] = tokenStreams[i]
    return {
        "token_streams": converted_token_stream,
        "freq": np.array(freq),
        "lengths": lengths,
    }


def build_similarity_matrix(freq: np.ndarray) -> np.ndarray:
    # alpha is how heavily matching tokens should be penalized, beta is how heavily
    # mismatching tokens should be rewarded. alpha + beta = 1
    alpha = 0.65
    beta = 0.35
    matrixLen = len(freq) + 1
    matrix = np.zeros((matrixLen, matrixLen))
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
            matrix[i, j] = int(1000 * value)
            matrix[j, i] = int(1000 * value)
    return np.array(matrix)


def build_self_similarities(token_streams: np.ndarray, matrix: np.ndarray, lengths: np.ndarray) -> np.ndarray:
    self_similarities = []
    for i in range(len(token_streams)):
        score = 0
        # for each token, find value of matching that token with itself and add to sum
        for tok in token_streams[i, : lengths[i]]:
            score += matrix[int(tok), int(tok)]
        self_similarities.append(score)
    return np.array(self_similarities, dtype=np.int32)


def run_comparisons(
    token_streams: np.ndarray,
    similarity_matrix: np.ndarray,
    self_similarities: np.ndarray,
    lengths: np.ndarray,
) -> np.ndarray:
    similarity_scores = np.zeros((len(token_streams), len(token_streams)))
    for i in range(len(token_streams)):
        for j in range(i + 1, len(token_streams)):
            similarity = get_similarity(
                token_streams[i, : lengths[i]],
                token_streams[j, : lengths[j]],
                similarity_matrix,
                self_similarities[i] + self_similarities[j],
            )
            similarity_scores[i, j] = similarity
    return similarity_scores


def convert_results(results: np.ndarray, files: List[Path]) -> dict:
    converted_results = {}
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            converted_results[frozenset((files[i], files[j]))] = results[i, j]
    return converted_results
