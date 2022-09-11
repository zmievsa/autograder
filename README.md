<p align="center">
  <a href="https://ovsyanka83.github.io/autograder/"><img src="https://raw.githubusercontent.com/Ovsyanka83/autograder/main/docs/_media/logo_with_text.svg" alt="AutoGrader"></a>
</p>
<p align="center">
  <b>Provides a simple, secure, and configurable way to grade programming assignments</b>
</p>

---

<p align="center">
<a href="https://github.com/ovsyanka83/autograder/actions?query=workflow%3ATests+event%3Apush+branch%3Amain" target="_blank">
    <img src="https://github.com/Ovsyanka83/autograder/actions/workflows/test.yaml/badge.svg?branch=main&event=push" alt="Test">
</a>
<a href="https://codecov.io/gh/ovsyanka83/autograder" target="_blank">
    <img src="https://img.shields.io/codecov/c/github/ovsyanka83/autograder?color=%2334D058" alt="Coverage">
</a>
<a href="https://pypi.org/project/assignment-autograder/" target="_blank">
    <img alt="PyPI" src="https://img.shields.io/pypi/v/assignment-autograder" alt="Package version">
</a>
<a href="https://pypi.org/project/assignment-autograder/" target="_blank">
    <img src="https://img.shields.io/pypi/pyversions/assignment-autograder" alt="Supported Python versions">
</a>
</p>

## Features

* Blazingly fast (can grade hundreads of submissions using dozens of testcases in a few minutes. Seconds if grading python)
* [Easy to grade](https://ovsyanka83.github.io/autograder/#/?id=usage)
* [Easy-to-write testcases](https://ovsyanka83.github.io/autograder/#/?id=writing-testcases)  
* Testcase grade can be based on [student's stdout](https://ovsyanka83.github.io/autograder/#/?id=helper-functions)
* Can grade C, C++, Java, and Python code in regular mode
* Can grade any programming language in stdout-only mode
* A file with testcase grades and details can be generated for each student
* You can customize the total points for the assignment, maximum running time of student's program, file names to be considered for grading, formatters for checking student stdout, and [so much more](https://github.com/Ovsyanka83/autograder/blob/master/autograder/default_config.toml).
* [Anti Cheating capabilities](https://ovsyanka83.github.io/autograder/#/?id=anti-cheating) that make it nearly impossible for students to cheat
* Grading submissions in multiple programming languages at once
* JSON result output supported if autograder needs to be integrated as a part of a larger utility
* Can check submissions for similarity (plagiarism)
* Can detect and report memory leaks in C/C++ code

## Installation

* Run `pip install assignment-autograder`
* To grade various programming languages, you'd need to install:
  * `gcc`/`clang` for C/C++ support
  * `Java JDK` for java support
  * `make` for compiled stdout-only testcase support
  * Any interpreter/compiler necessary to run stdout-only testcases. For example, testcases with ruby in their shebang lines will require the ruby interpreter

### Updates

`pip install -U --no-cache-dir assignment-autograder`

## Quickstart

* Run `autograder guide path/to/directory/you'd/like/to/grade`. The guide will create all of the necessary configurations and directories for grading and will explain how to grade.
* Read the [usage](https://ovsyanka83.github.io/autograder/#/?id=usage) section of the docs

## Supported Platforms

* Linux is fully supported
* OS X is fully supported
* Windows is partially supported:
  * Stdout-testcases that require shebang lines are not and cannot be supported

## Supported Programming Languages

* Java
* C
* C++
* CPython (3.8-3.11)
* Any programming language if stdout-only grading is used
