#include <stdlib.h>
#include <stdio.h>
 
int main(void)
{
    int i;
    char *s;
 
    s = " -9885";
    i = atoi(s);     /* i = -9885 */
 
    printf("i = %d\n",i);
}
 
/*******************  Output should be similar to:  ***************
 
i = -9885
*/
