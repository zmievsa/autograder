CC=gcc
CFLAGS=-std=c99
OBJS=mem.o
HEADERS=mem.h

all: libmemd.a test 

%.o: %.c $(HEADERS)
	$(CC) $(CFLAGS) -c -o $@ $<
libmemd.a: $(OBJS) 
	ar rcs libmemd.a $(OBJS)
test: test.o libmemd.a $(HEADERS)
	gcc -L. -o test test.o -lmemd
clean:
	rm $(OBJS)
	rm libmemd.a
	rm test 
	
