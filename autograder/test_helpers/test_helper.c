#include <stdlib.h>

int RESULT_EXIT_CODES[] = {{% RESULT_EXIT_CODES %}};

#define CHECK_OUTPUT() exit({% CHECK_OUTPUT_EXIT_CODE %})
#define RESULT(r) exit(RESULT_EXIT_CODES[r])
#define PASS() RESULT(100)
#define FAIL() RESULT(0)