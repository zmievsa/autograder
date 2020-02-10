#include <stdio.h>


int main()
{
    int arr2[5] = {1, 3, 9, 27, 81};
    int arr2_final[5] = {0, -3, 0, -27, 0};
	AdjustArray(arr2, 5);
    int testfailed = 0;
    for (int i = 0; i < 5; i++) {
        if (arr2[i] != arr2_final[i]) testfailed = 1;
    }
    if (!testfailed) printf("PASS");
	return 0;
}

