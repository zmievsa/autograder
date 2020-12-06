#include <stdlib.h>

// Static modifier and pre-processing keep these functions and array private
// to the testcase file.


static int RESULT_EXIT_CODES[] = {{% RESULT_EXIT_CODES %}};

void CHECK_OUTPUT() {
  exit({% CHECK_OUTPUT_EXIT_CODE %})
}
static void RESULT(int r) {
  exit(RESULT_EXIT_CODES[r])
}
static void PASS() {
  RESULT(100)
}
static void FAIL() {
  RESULT(0)
}
