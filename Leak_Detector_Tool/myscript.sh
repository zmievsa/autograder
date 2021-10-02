#!/bin/bash
file=$1
gcc -c leak_detector_c.c
gcc -c $file
gcc -o memtest leak_detector_c.o ${file%.*}.o
./memtest
cat leak_info.txt
