#include <stdlib.h>
#include <stdio.h>

void test_env()
{
    printf("\n%s", getenv("VALIDATING_STRING"));
    exit(103);
}

void test_exit()
{
    exit(103);
}
// We don't test for import because the file will not even compile if it tries to use methods that are not visible to it