#include <stdlib.h>

#define CHECK_OUTPUT() exit({% CHECK_OUTPUT_EXIT_CODE %})
#define RESULT(r) exit(r+({% RESULT_EXIT_CODE_SHIFT %}))
#define PASS() exit({% MAX_RESULT %})
#define FAIL() exit({% MIN_RESULT %})