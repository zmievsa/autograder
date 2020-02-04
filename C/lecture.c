// void printNumbers() 
// { 
//     int n = 1; 
// label: 
//     printf("%d ",n); 
//     n++; 
//     if (n <= 10) 
//         goto label; 
// }

/*
 * Statements
 ** Summary
 ** If/else if/else/switch
 *** switch break
 * Do while loop
 * Goto
 * Mobaxterm, gcc, linux!
 * 
*/
#include <stdio.h>


int main() {
    int i = 1;

    do {
        printf("i = %d ", i);
        i++;
    } while (i < 3);
    printf("\n");
}
