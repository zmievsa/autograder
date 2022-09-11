#include <stdlib.h>
#include <stdio.h>

void test_env()
{
    printf("\n100$%s", getenv("VALIDATING_STRING"));
    exit(3);
}

// The student might hope to get successful on an empty stdout check
void test_exit()
{
    exit(4);
}
// We don't test for import because the file will not even compile if it tries to use methods that are not visible to it