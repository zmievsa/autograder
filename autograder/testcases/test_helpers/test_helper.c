#include <stdlib.h>
#include <stdio.h>

// Static modifier and pre-processing keep these functions and array private
// to the testcase file.

static void CHECK_OUTPUT()
{
  printf("\n{ % VALIDATING_STRING % }");
  exit({ % CHECK_OUTPUT_EXIT_CODE % });
}
static void RESULT(int r)
{
  printf("\n{ % VALIDATING_STRING % }");
  exit(r + { % RESULT_EXIT_CODE_OFFSET % });
}
static void PASS()
{
  RESULT(100);
}
static void FAIL()
{
  RESULT(0);
}
