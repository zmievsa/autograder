// A simple example in C
// Source: Wikipedia Page for Memory leak

#include <stdlib.h>

void function_which_allocates(void) {
    /* allocate an array of 45 floats */
    float *a = malloc(sizeof(float) * 45);

    /* additional code making use of 'a' */

    /* return to main, having forgotten to free the memory we malloc'd */
}

int main(void) {
    function_which_allocates();

    /* the pointer 'a' no longer exists, and therefore cannot be freed,
     but the memory is still allocated. a leak has occurred. */
}
