#include <stdlib.h>

// Static modifier and pre-processing keep these functions and array private
// to the testcase file.


static int RESULT_EXIT_CODES[] = {{% RESULT_EXIT_CODES %}};

#define CHECK_OUTPUT() exit({% CHECK_OUTPUT_EXIT_CODE %})
#define RESULT(r) exit(RESULT_EXIT_CODES[r])
#define PASS() RESULT(100)
#define FAIL() RESULT(0)