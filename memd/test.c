#include <stdlib.h>
#include "mem.h"

int main() {
	void *p1, *p2;

	//Malloc test
	p1 = malloc(10);
	p2 = malloc(20); //Leaky
	free(p1);

	//Calloc test
	p1 = calloc(5, 10);
	p2 = calloc(5, 20); //Leaky
	free(p1);

	//Realloc test
	p1 = malloc(10);
	p1 = realloc(p1, 20);

	p2 = malloc(20);
	p2 = realloc(p2, 30); //Leaky

	free(p1);
}
