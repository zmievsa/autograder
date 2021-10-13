#!/bin/bash
file=$1

cp $file tmp.${file##*.}
temp=tmp.${file##*.}

case "$temp" in
*.c)
    gcc -c leak_detector_c.c
    gcc -c $temp
    gcc -o memtest leak_detector_c.o ${temp%.*}.o
    ./memtest > /dev/null 2>&1
    cat leak_info.txt
    rm memtest leak_detector_c.o ${temp%.*}.o $temp
    ;;
*.cpp | *.c++ | *.cc | *.cxx | *.CPP | *.cp | *.C)
    g++ -c leak_detector_c.c
    g++ -c $temp
    g++ -o memtest leak_detector_c.o ${temp%.*}.o
    ./memtest > /dev/null 2>&1
    cat leak_info.txt
    rm memtest leak_detector_c.o ${temp%.*}.o $temp
    ;;
*)
    echo "Invalid source file name"
    exit 1
esac