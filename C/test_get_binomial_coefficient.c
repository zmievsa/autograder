#include <stdio.h>


int main()
{
	if (GetBinomialCoefficient(0, 0) == 1) printf("PASS\n");
	if (GetBinomialCoefficient(4, 3) == 4) printf("PASS\n");
	return 0;
}