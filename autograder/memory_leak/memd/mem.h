void *debug_malloc(size_t size, const char* file, int line);
void *debug_calloc(size_t count, size_t size, const char* file, int line);
void *debug_realloc(void *ptr, size_t size, const char* file, int line);
void debug_free(void *p, const char* file, int line);

#define malloc(s) debug_malloc(s, __FILE__, __LINE__)
#define calloc(c, s) debug_calloc(c, s, __FILE__, __LINE__)
#define realloc(p, s) debug_realloc(p, s, __FILE__, __LINE__)
#define free(p) debug_free(p, __FILE__, __LINE__)
