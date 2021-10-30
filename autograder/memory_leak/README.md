# Memory Leak Detection
- This README is in works. Just a brief overview of the commands and output.

## Terminal Commands
1. chmod +x memleak.sh
2. ./memleak.sh `path/to/file`
   - Example: ./memleak.sh tests/example.c

## Note These Following Details
- All memory leak information/summary is located in some .txt file (after running bash script).
- All sources codes needs to be in a directory.
- Person does not need to modify their source code in order to use this tool.

Contents of `example.c`
```c
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    char *ptr1; 
    int *ptr2; 

    ptr1 = malloc(sizeof(char) * 10); // allocating 10 bytes        
    ptr2 = calloc(20, sizeof(int)); // allocating 80 bytes 
    return 0;
}
```

Expected Output after running `chmod +x memleak.sh && ./memleak.sh tests/example.c` (Note that "address" may differ)
```txt
Memory Leak Summary
-----------------------------------
address : 0x55890296b2a0
size    : 10 bytes
file    : example.c
line    : 8
-----------------------------------
address : 0x55890296b3e0
size    : 80 bytes
file    : example.c
line    : 9
-----------------------------------
```
