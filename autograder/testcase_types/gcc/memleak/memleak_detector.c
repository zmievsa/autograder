/*
 * leak_detector_c.c: based on code by Rabinarayan Biswal, 27 Jun 2007
 * (http://www.codeproject.com/Articles/19361/Memory-Leak-Detection-in-C)
 * Modified by Faizar Ali for Autograder project
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include "memleak_detector.h"

#undef malloc
#undef calloc
#undef realloc
#undef free

static MEM_LEAK *ptr_start = NULL;
static MEM_LEAK *ptr_next = NULL;

static void __add_new_memleak_entry__(MEM_INFO alloc_info)
{
    MEM_LEAK *mem_leak_info = NULL;
    mem_leak_info = (MEM_LEAK *)malloc(sizeof(MEM_LEAK));
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
    else
    {
        ptr_next->next = mem_leak_info;
        ptr_next = ptr_next->next;
    }
}

static void __remove_memleak_entry__(unsigned pos)
{
    unsigned index = 0;
    MEM_LEAK *alloc_info, *temp;

    temp = ptr_start;

    while (temp->next != NULL)
        temp = temp->next;
    ptr_next = temp;

    if (pos == 0)
    {
        MEM_LEAK *temp = ptr_start;
        ptr_start = ptr_start->next;
        free(temp);
    }
    else
    {
        for (index = 0, alloc_info = ptr_start; index < pos; alloc_info = alloc_info->next, ++index)
        {
            if (pos == index + 1)
            {
                temp = alloc_info->next;
                if (ptr_next == temp)
                {
                    ptr_next = alloc_info;
                    alloc_info->next = NULL;
                }
                else
                    alloc_info->next = temp->next;
                free(temp);
                break;
            }
        }
    }
}

static void __clear_memleak_entries__(void)
{
    MEM_LEAK *temp = ptr_start;
    MEM_LEAK *alloc_info = ptr_start;

    while (alloc_info != NULL)
    {
        alloc_info = alloc_info->next;
        free(temp);
        temp = alloc_info;
    }
}

// replacement of malloc
void *xmalloc(unsigned int size, const char *file, unsigned int line)
{
    void *ptr = malloc(size);

    if (ptr == NULL && size != 0)
    {
        fprintf(stderr, "Memleak Detector: memory exhausted\n");
        exit(1);
    }

    if (ptr != NULL && strcmp(strrchr(file, '.'), ".h") != 0)
        add_mem_info(ptr, size, file, line);
    return ptr;
}

// replacement of calloc
void *xcalloc(unsigned int elements, unsigned int size, const char *file, unsigned int line)
{
    unsigned total_size;
    void *ptr = calloc(elements, size);

    if (ptr == NULL && size != 0)
    {
        fprintf(stderr, "Memleak Detector: memory exhausted\n");
        exit(1);
    }

    if (ptr != NULL && strcmp(strrchr(file, '.'), ".h") != 0)
    {
        total_size = elements * size;
        add_mem_info(ptr, total_size, file, line);
    }
    return ptr;
}

// replacement of realloc
void *xrealloc(void *ptr, size_t size, const char *file, unsigned int line)
{
    void *ptr_new = realloc(ptr, size);

    if (ptr_new == NULL && size != 0)
    {
        fprintf(stderr, "Memleak Detector: memory exhausted\n");
        exit(1);
    }

    if (ptr_new != NULL && strcmp(strrchr(file, '.'), ".h") != 0)
    {
        remove_mem_info(ptr);
        add_mem_info(ptr_new, size, file, line);
    }
    return ptr_new;
}

// replacement of free
void xfree(void *mem_ref)
{
    remove_mem_info(mem_ref);
    free(mem_ref);
}

// gets the allocated memory info and adds it to a list
static void add_mem_info(void *mem_ref, unsigned int size, const char *file, unsigned int line)
{
    MEM_INFO mem_alloc_info;

    // if file is from a .h header, don't add it to list
    if (strcmp(strrchr(file, '.'), ".h") == 0)
        return;

    // fill up the structure with all info
    memset(&mem_alloc_info, 0, sizeof(mem_alloc_info));
    mem_alloc_info.address = mem_ref;
    mem_alloc_info.size = size;
    strncpy(mem_alloc_info.file_name, file, FILE_NAME_LENGTH);
    mem_alloc_info.line = line;

    // add the above info to a list
    __add_new_memleak_entry__(mem_alloc_info);
}

// if the allocated memory info is part of the list, removes it
static void remove_mem_info(void *mem_ref)
{
    unsigned short index;
    MEM_LEAK *leak_info = ptr_start;

    // check if allocate memory is in our list
    for (index = 0; leak_info != NULL; ++index, leak_info = leak_info->next)
    {
        if (leak_info->mem_info.address == mem_ref)
        {
            __remove_memleak_entry__(index);
            break;
        }
    }
}

// helper function to convert file descriptor into a file
static void configure_memleak(char *fname)
{
    unsigned short index;
    MEM_LEAK *leak_info;

    FILE *fp_write = fopen(fname, "w");

    if (fp_write == NULL)
    {
        fprintf(stderr, "\nMemleak Detector: cannot create or open file!\n");
    }

    if (ptr_start == NULL)
    {
        fclose(fp_write);
        return;
    }

    fprintf(fp_write, "%s\n", "-----------------------------------");

    for (leak_info = ptr_start; leak_info != NULL; leak_info = leak_info->next)
    {
        fprintf(fp_write, "address : %p\n", leak_info->mem_info.address);
        fprintf(fp_write, "size    : %d bytes\n", leak_info->mem_info.size);
        fprintf(fp_write, "file    : %s\n", leak_info->mem_info.file_name);
        fprintf(fp_write, "line    : %d\n", leak_info->mem_info.line);
        fprintf(fp_write, "%s\n", "-----------------------------------");
    }
    fclose(fp_write);
}

// Writes all info of the unallocated memory into a file
// at the end of program execution
static void report_memleak(void)
{
    configure_memleak(getenv("MEMLEAK_FILE"));
    __clear_memleak_entries__();
}
