#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char * ptr1; 
    int * ptr2; 
    float * ptr3;

    ptr1 = (char *) malloc (10); // allocating 10 bytes        
    ptr2 = (int *) calloc (10, sizeof(int)); 	// allocating 40 bytes 
    ptr3 = (float *) calloc (15, sizeof(float)); // allocating 60 bytes
    printf("Hello World\n");
    free(ptr2);
    return 0;
}
