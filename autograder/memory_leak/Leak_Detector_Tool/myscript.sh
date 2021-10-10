#!/bin/bash
file=$1

case "$file" in
*.c)
  gcc -c leak_detector_c.c
  gcc -c $file
  gcc -o memtest leak_detector_c.o ${file%.*}.o
  ./memtest > /dev/null 2>&1
  cat leak_info.txt
  rm *.o
  ;;
*.cpp | *.c++ | *.cc | *.cxx)
  g++ -c leak_detector_c.c
  g++ -c $file
  g++ -o memtest leak_detector_c.o ${file%.*}.o
  ./memtest > /dev/null 2>&1
  cat leak_info.txt
  rm *.o
  ;;
*)
  echo "Invalid source file name"
  exit 1
esac
