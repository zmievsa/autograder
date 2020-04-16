#include <stdlib.h>

#define NO_RESULT() exit({% RESULTLESS_EXIT_CODE %})
#define RESULT(r) exit(r+({% RESULT_EXIT_CODE_SHIFT %}))
#define PASS() exit({% MAX_RESULT %})
#define FAIL() exit({% MIN_RESULT %})