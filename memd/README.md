## Introduction
This is a very simple memory leak detector for C. It uses the file system
as a database and stores information about any memory that
is allocated in files. As memory is freed these files are deleted.
Any file left behind after the program exists indicates memory leak.

## How to Use

1. Simply include ``mem.h`` from C files where memory 
is managed  using ``malloc``, ``calloc``, ``realloc`` and ``free``.
2. Link this library (``libmemd.a``) to the executable.

Example:

```c
#include <stdlib.h>
#include "mem.h"

int main() { 
        void *p;
        
        p = malloc(10); //This will leak
}
```

Run the executable. For each unfreed memory buffer, a .mem file will be 
created. For example if memory address ``0x7fb1d2403960`` leaks, then a file 
called ``0x7fb1d2403960.mem`` will be left behind after the application exits.

The file will have information about where the memory was allocated and
the size of the buffer. For example:

```text
File: test.c
Line: 7
Size: 10 bytes
```

## Double Free Detection
Both ``free`` and ``realloc`` function will be checked for double free scenario. If a double free is detected you will see message like this in the console:

```text
Double free: 0x7fafb35009e0 File: Dictionary.c Line: 45
```
