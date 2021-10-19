#!/bin/bash
file=$1

cp $file ./
file=$(basename $file)

case "$file" in
*.c)
    gcc -c leak_detector_c.c
    gcc -c $file
    gcc -o memtest leak_detector_c.o ${file%.*}.o
    ;;
*.cpp | *.c++ | *.cc | *.cxx | *.CPP | *.cp | *.C)
    gcc -c leak_detector_c.c
    g++ --std=c++11 -c $file
    g++ --std=c++11 -o memtest leak_detector_c.o ${file%.*}.o
    ;;
*)
    echo "Invalid source file name"
    exit 1
esac

./memtest > /dev/null 2>&1
sed -i 's/\x0//g' leak_info.txt
cat leak_info.txt
rm memtest leak_detector_c.o ${file%.*}.o $file
