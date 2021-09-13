import sys
from antlr4 import *
from lexers.Java8Lexer import JavaLexer
from lexers.Python3Lexer import Python3Lexer

def compare(files):
    numFiles = len(files)
    # add error handling
    if numFiles == 0:
        return "No files found"
    prev = files[0].name.split('.')[1]
    for i in range(numFiles):
        fileType = files[i].name.split('.')[1]
        if fileType != prev:
            return "File types don't match"
        prev = fileType
        if fileType == "java":
            lexerClass = JavaLexer
            # ignore comments
            ignoreList = [107]
        elif fileType == "py":
            lexerClass = Python3Lexer
            # ignore comments and new lines
            ignoreList = [-1, 39]
        else:
            return "This file type is not supported"
    similarityScores = [[0 for x in range(numFiles)] for y in range(numFiles)]
    tokenStreams = []
    for i in range(numFiles):
        stream = InputStream(files[i].read())
        files[i].close()
        lexer = lexerClass(stream)
        tokens = CommonTokenStream(lexer)
        tokens.fetch(500)
        array = []
        for token in tokens.tokens:
            # remove comments
            print(token.type)
            if token.type not in ignoreList:
                array += [str(token.type)]
        tokenStreams += [array]
    for i in range(numFiles):
        for j in range(i + 1, numFiles):
            similarity = getSimilarity(tokenStreams[i], tokenStreams[j])
            similarityScores[i][j] = similarity
            similarityScores[j][i] = similarity
    return similarityScores

def getSimilarity(a, b):
    minLen = min(len(a), len(b))
    numberSame = 0
    for i in range(minLen):
        if a[i] == b[i]:
            numberSame = numberSame + 1
    return numberSame / minLen
