#include <stdio.h>
#include <stdlib.h>
#include "leak_detector_c.h"

int main(void) {
    char *ptr1; 
    int *ptr2; 

    ptr1 = (char *) malloc(sizeof(char) * 10); // allocating 10 bytes        
    ptr2 = (int *) calloc(20, sizeof(int)); // allocating 80 bytes 
    return 0;
}
