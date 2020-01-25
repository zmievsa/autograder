#include <stdio.h>


int main()
{
	if (SumOfDigits(0) == 0) printf("PASS\n");
	if (SumOfDigits(91854672) == 42) printf("PASS\n");
	if (SumOfDigits(-1) == 2+1+4+7+4+8+3+6+4+7) printf("PASS\n");
	return 0;
}

