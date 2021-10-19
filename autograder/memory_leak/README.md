# Memory Leak Detection
- This README is in works. Just a brief overview of the commands and output.

## Terminal Commands
1. chmod +x memleak.sh
2. ./memleak.sh `path/to/file`
   - Example: ./memleak.sh tests/example.c

## Note These Following Details
- You must `#include "leak_detector_c.h"` in your code
- All memory leak information/summary is located in `leak_info.txt` (after running bash script)
- All sources codes needs to be in a directory.

Contents of `example.c`
```c
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
```

Expected Output after running `chmod +x memleak.sh && ./memleak.sh tests/example.c` (Note that "address" may differ)
```txt
Memory Leak Summary
-----------------------------------
address : 0x558f200be2a0
size    : 10 bytes
file    : example.c
line    : 9
-----------------------------------
address : 0x558f200be3e0
size    : 80 bytes
file    : example.c
line    : 10
-----------------------------------
```

