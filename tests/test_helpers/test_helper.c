#include <stdlib.h>

#define NO_RESULT exit(%d)
#define RESULT(r) exit(r+(%d))
#define PASS      exit(%d)
#define FAIL      exit(%d)