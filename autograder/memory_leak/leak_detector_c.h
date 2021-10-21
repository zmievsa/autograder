// leak_detector_c.h: based on code by Rabinarayan Biswal, 27 Jun 2007
// (http://www.codeproject.com/Articles/19361/Memory-Leak-Detection-in-C)

#ifdef __cplusplus
extern "C" {
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifndef  LEAK_DETECTOR_C_H
#define  LEAK_DETECTOR_C_H

#define  FILE_NAME_LENGTH           256
#define  OUTPUT_FILE                "leak_info.txt"
#define  malloc(size)               xmalloc(size, __FILE__, __LINE__)
#define  calloc(elements, size)     xcalloc(elements, size, __FILE__, __LINE__)
#define  realloc(ptr, size)         xrealloc(ptr, size, __FILE__, __LINE__)
#define  free(mem_ref)              xfree(mem_ref)

typedef struct _MEM_INFO {
    void            *address;
    unsigned int    size;
    char            file_name[FILE_NAME_LENGTH];
    unsigned int    line;
} MEM_INFO;

typedef struct _MEM_LEAK {
    MEM_INFO mem_info;
    struct _MEM_LEAK * next;
} MEM_LEAK;

static void add(MEM_INFO alloc_info);
static void erase(unsigned pos);
static void clear(void);

void * xmalloc(unsigned int size, const char * file, unsigned int line);
void * xcalloc(unsigned int elements, unsigned int size, const char * file, unsigned int line);
void * xrealloc(void *ptr, size_t size, const char * file, unsigned int line);
void xfree(void * mem_ref);

static void add_mem_info (void * mem_ref, unsigned int size,  const char * file, unsigned int line);
static void remove_mem_info (void * mem_ref);
static void report_mem_leak(void);

void __attribute__((destructor)) report_mem_leak();

#endif
#ifdef __cplusplus
}
#endif
