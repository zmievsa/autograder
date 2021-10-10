#include <stdio.h>
#include <stdlib.h>
#include "leak_detector_c.h"

int main(void) {
    char * ptr1; 
    int * ptr2; 
    float * ptr3;

    atexit(report_mem_leak);

    ptr1 = (char *) malloc (10); // allocating 10 bytes        
    printf("Banana\n");
    ptr2 = (int *) calloc (10, sizeof(int)); 	// allocating 40 bytes 
    
    ptr3 = (float *) calloc (15, sizeof(float)); // allocating 60 bytes
    printf("Hello World\n");
    printf("Apple\n");
    free(ptr2);
    return 0;
}
