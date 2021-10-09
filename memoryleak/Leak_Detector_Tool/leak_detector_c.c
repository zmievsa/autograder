#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "leak_detector_c.h"

#undef malloc
#undef calloc
#undef free


static MEM_LEAK * ptr_start = NULL;
static MEM_LEAK * ptr_next =  NULL;


//void * xmalloc (unsigned int size, const char * file, unsigned int line);
//void * xcalloc (unsigned int elements, unsigned int size, const char * file, unsigned int line);
//void xfree(void * mem_ref);
/*
 * adds allocated memory info. into the list
 *
 */
void add(MEM_INFO alloc_info)
{

	MEM_LEAK * mem_leak_info = NULL;
	mem_leak_info = (MEM_LEAK *) malloc (sizeof(MEM_LEAK));
	mem_leak_info->mem_info.address = alloc_info.address;
	mem_leak_info->mem_info.size = alloc_info.size;
	strcpy(mem_leak_info->mem_info.file_name, alloc_info.file_name);
	mem_leak_info->mem_info.line = alloc_info.line;
	mem_leak_info->next = NULL;

	if (ptr_start == NULL)
	{
		ptr_start = mem_leak_info;
		ptr_next = ptr_start;
	}
	else {
		ptr_next->next = mem_leak_info;
		ptr_next = ptr_next->next;
	}

}

/*
 * erases memory info. from the list
 *
 */
// void erase(unsigned pos)
// {

// 	unsigned index = 0;
// 	MEM_LEAK * alloc_info, * temp;

// 	if(pos == 0)
// 	{
// 		MEM_LEAK * temp = ptr_start;
// 		ptr_start = ptr_start->next;
// 		free(temp);
// 	}
// 	else
// 	{
// 		for(index = 0, alloc_info = ptr_start; index < pos;
// 			alloc_info = alloc_info->next, ++index)
// 		{
// 			if(pos == index + 1)
// 			{
// 				temp = alloc_info->next;
// 				alloc_info->next =  temp->next;
// 				free(temp);
// 				break;
// 			}
// 		}
// 	}
// }

void erase(unsigned pos)
{
    unsigned index = 0;
    MEM_LEAK* alloc_info, * temp;

    temp = ptr_start;
    while (temp->next != NULL) {
        temp = temp->next;
    }
    ptr_next = temp;

    if (pos == 0) {
        MEM_LEAK * temp = ptr_start;
        ptr_start = ptr_start->next;
        free(temp);
    } else {
        for (index = 0, alloc_info = ptr_start; index < pos;
            alloc_info = alloc_info->next, ++index)
        {
            if (pos == index + 1) {
                temp = alloc_info->next;
                if (ptr_next == temp) {
                    ptr_next = alloc_info;
                    alloc_info->next =  NULL;
                } else {
                    alloc_info->next = temp->next;
                }
                free(temp);
                break;
            }
        }
    }
}

/*
 * deletes all the elements from the list
 */
void clear()
{
	MEM_LEAK * temp = ptr_start;
	MEM_LEAK * alloc_info = ptr_start;

	while(alloc_info != NULL)
	{
		alloc_info = alloc_info->next;
		free(temp);
		temp = alloc_info;
	}
}

/*
 * replacement of malloc
 */
void * xmalloc (unsigned int size, const char * file, unsigned int line)
{
	void * ptr = malloc (size);
	if (ptr != NULL)
	{
		add_mem_info(ptr, size, file, line);
	}
	return ptr;
}

/*
 * replacement of calloc
 */
void * xcalloc (unsigned int elements, unsigned int size, const char * file, unsigned int line)
{
	unsigned total_size;
	void * ptr = calloc(elements , size);
	if(ptr != NULL)
	{
		total_size = elements * size;
		add_mem_info (ptr, total_size, file, line);
	}
	return ptr;
}


/*
 * replacement of free
 */
void xfree(void * mem_ref)
{
	remove_mem_info(mem_ref);
	free(mem_ref);
}

/*
 * gets the allocated memory info and adds it to a list
 *
 */
void add_mem_info (void * mem_ref, unsigned int size,  const char * file, unsigned int line)
{
	MEM_INFO mem_alloc_info;

	/* fill up the structure with all info */
	memset( &mem_alloc_info, 0, sizeof ( mem_alloc_info ) );
	mem_alloc_info.address 	= mem_ref;
	mem_alloc_info.size = size;
	strncpy(mem_alloc_info.file_name, file, FILE_NAME_LENGTH);
	mem_alloc_info.line = line;

	/* add the above info to a list */
	add(mem_alloc_info);
}

/*
 * if the allocated memory info is part of the list, removes it
 *
 */
void remove_mem_info (void * mem_ref)
{
	unsigned short index;
	MEM_LEAK  * leak_info = ptr_start;

	/* check if allocate memory is in our list */
	for(index = 0; leak_info != NULL; ++index, leak_info = leak_info->next)
	{
		if ( leak_info->mem_info.address == mem_ref )
		{
			erase ( index );
			break;
		}
	}
}

/*
 * writes all info of the unallocated memory into a file
 */
void report_mem_leak(void)
{
	unsigned short index;
	MEM_LEAK * leak_info;

	FILE * fp_write = fopen (OUTPUT_FILE, "wt");
	char info[1024];

	if(fp_write != NULL)
	{
		sprintf(info, "%s\n", "Memory Leak Summary");
		fwrite(info, (strlen(info) + 1) , 1, fp_write);
		sprintf(info, "%s\n", "-----------------------------------");
		fwrite(info, (strlen(info) + 1) , 1, fp_write);

		for(leak_info = ptr_start; leak_info != NULL; leak_info = leak_info->next)
		{
			sprintf(info, "address : %p\n", leak_info->mem_info.address);
			fwrite(info, (strlen(info) + 1) , 1, fp_write);
			sprintf(info, "size    : %d bytes\n", leak_info->mem_info.size);
			fwrite(info, (strlen(info) + 1) , 1, fp_write);
			sprintf(info, "file    : %s\n", leak_info->mem_info.file_name);
			fwrite(info, (strlen(info) + 1) , 1, fp_write);
			sprintf(info, "line    : %d\n", leak_info->mem_info.line);
			fwrite(info, (strlen(info) + 1) , 1, fp_write);
			sprintf(info, "%s\n", "-----------------------------------");
			fwrite(info, (strlen(info) + 1) , 1, fp_write);
		}
	}
	clear();
}
