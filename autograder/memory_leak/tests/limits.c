// C program to implement
// the above approach
#include <limits.h>
#include <stdio.h>
 
// Driver code
int main()
{
    printf("Number of bits in a byte %d\n",
           CHAR_BIT);
    printf("Minimum value of SIGNED CHAR = %d\n",
           SCHAR_MIN);
    printf("Maximum value of SIGNED CHAR = %d\n",
           SCHAR_MAX);
    printf("Maximum value of UNSIGNED CHAR = %d\n",
           UCHAR_MAX);
    printf("Minimum value of SHORT INT = %d\n",
           SHRT_MIN);
    printf("Maximum value of SHORT INT = %d\n",
           SHRT_MAX);
    printf("Minimum value of INT = %d\n",
           INT_MIN);
    printf("Maximum value of INT = %d\n",
           INT_MAX);
    printf("Minimum value of CHAR = %d\n",
           CHAR_MIN);
    printf("Maximum value of CHAR = %d\n",
           CHAR_MAX);
    printf("Minimum value of LONG = %ld\n",
           LONG_MIN);
    printf("Maximum value of LONG = %ld\n",
           LONG_MAX);
    return (0);
}
