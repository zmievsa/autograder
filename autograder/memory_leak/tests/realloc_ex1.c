#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "leak_detector_c.h"

int main () {
    char *str;
    char *str2;

    /* Initial memory allocation */
    str = (char *) malloc(15);
    str2 = (char *) malloc(20);
    strcpy(str, "tutorialspoint");
    printf("String = %s,  Address = %p\n", str, str);
    strcpy(str2, "tutorialspoint");
    printf("String = %s,  Address = %p\n", str2, str2);


    /* Reallocating memory */
    str = (char *) realloc(str, 25);
    strcat(str, ".com");
    printf("String = %s,  Address = %p\n", str, str);

    str2 = (char *) realloc(str2, 25);
    strcat(str2, ".com");
    printf("String = %s,  Address = %p\n", str2, str2);

    free(str);
    // free(str2);

    return(0);
}