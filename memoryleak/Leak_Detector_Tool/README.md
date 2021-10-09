# Memory Leak Detection
- This README is in works. Just a brief overview of the commands and output.

## Terminal Commands
1. chmod +x myscript.sh
2. ./myscript.sh *file name*
   - Example: ./myscript.sh test2.c

test2.c
```c
#include <malloc.h>
#include <stdio.h>
#include <stdlib.h>
#include "leak_detector_c.h" // Note this

int main(void) 
{
    char * ptr1; 
    int * ptr2; 
    float * ptr3;

    atexit(report_mem_leak); // Note this

    ptr1 = (char *) malloc (10); // allocating 10 bytes        
    printf("Banana\n");
    ptr2 = (int *) calloc (10, sizeof(int)); 	// allocating 40 bytes 
    ptr3 = (float *) calloc (15, sizeof(float)); // allocating 60 bytes
    printf("Hello World\n");
    printf("Apple\n");
    free(ptr2);
    return 0;
}

```

Expected Output after running `chmod +x myscript.sh && ./myscript.sh test2.c` (Note that "address" may differ)
```txt
Banana
Hello World
Apple
Memory Leak Summary
-----------------------------------
address : 0x5631d6af02a0
size    : 10 bytes
file    : test2.c
line    : 14
-----------------------------------
address : 0x5631d6af0940
size    : 60 bytes
file    : test2.c
line    : 18
-----------------------------------

```

