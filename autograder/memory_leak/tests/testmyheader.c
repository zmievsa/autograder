// C program to use the above created header file
#include <stdio.h>
#include <stdlib.h>
#include "myheader.h"

int main()
{
    just_add(4, 6);
  
    /*This calls add function written in myhead.h  
      and therefore no compilation error.*/
    just_multiply(5, 5);
    
    int *ptr2 = malloc(sizeof(int) * 20);
    
    just_leak();
  
    // Same for the multiply function in myhead.h
    printf("BYE!See you Soon");
    return 0;
}
