#include <stdio.h>
#include <stdlib.h>

int main(void) {
    int *ptr = malloc(sizeof(int) * 20);
    printf("Hello World\n");
    free(ptr);
    return 0;
}
