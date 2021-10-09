#!/bin/bash

for dirname in examples/*; do
    echo y | python3 -m autograder run $dirname &
done