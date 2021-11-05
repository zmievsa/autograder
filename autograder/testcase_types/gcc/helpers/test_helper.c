#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#if defined(_WIN64) || defined(_WIN32)
int setenv(const char *name, const char *value, int overwrite)
{
  int errcode = 0;
  if (!overwrite)
  {
    size_t envsize = 0;
    errcode = getenv_s(&envsize, NULL, 0, name);
    if (errcode || envsize)
      return errcode;
  }
  return _putenv_s(name, value);
}
#endif

// This hack makes this function run before main which is a gcc-specific feature which effectively binds this
// implementation of autograder to gcc.
static void ENABLE_ANTI_CHEAT(void) __attribute__((constructor));

// Static modifier and pre-processing keep these functions/variables private to the testcase file.

// This 32 size might cause bugs in the future if we ever decide to make strings longer.
// If any bugs with validation happen, suspect this line.
static char VALIDATING_STRING[32] = {'\0'};

static void ENABLE_ANTI_CHEAT()
{
  if (strlen(VALIDATING_STRING) == 0)
    strcpy(VALIDATING_STRING, getenv("VALIDATING_STRING"));
  setenv("VALIDATING_STRING", "", 1);
}
static void CHECK_STDOUT()
{
  printf("\n-1{% SPLITCHAR %}%s", VALIDATING_STRING);
  exit({ % CHECK_STDOUT_EXIT_CODE % });
}
static void RESULT(double r)
{
  printf("\n%f{% SPLITCHAR %}%s", r, VALIDATING_STRING);
  exit({ % RESULT_EXIT_CODE % });
}
static void PASS()
{
  RESULT(100);
}
static void FAIL()
{
  RESULT(0);
}
