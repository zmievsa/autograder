/*
 * ex004.c
 */
 
 /*

Expected:

==2816== Heapusage - https://github.com/d99kris/heapusage
==2816== 
==2816== HEAP SUMMARY:
==2816==     in use at exit: 0 bytes in 0 blocks
==2816==   total heap usage: 1 allocs, 1 frees, 5555 bytes allocated
==2816==    peak heap usage: 5555 bytes allocated
==2816== 
==2816== LEAK SUMMARY:
==2816==    definitely lost: 0 bytes in 0 blocks
==2816== 

 */

/* ----------- Includes ------------------------------------------ */
#include <stdlib.h>


/* ----------- Global Functions ---------------------------------- */
int main(void)
{
  /* Allocate 1 block of 5555 bytes */
  void* ptr = malloc(5555);
  if (ptr == NULL)
  {
    return 1;
  }

  /* Free allocation */
  free(ptr);

  /* Free allocation again (double free) */
  // free(ptr);

  return 0;
}