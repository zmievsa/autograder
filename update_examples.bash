#!/bin/bash

for dirname in examples/*; do
    echo y | autograder run $dirname &
done