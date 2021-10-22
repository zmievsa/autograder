// It is not recommended to put function definitions 
// in a header file. Ideally there should be only
// function declarations. Purpose of this code is
// to only demonstrate working of header files.
void just_add(int a, int b)
{
    printf("Added value=%d\n", a + b);
}
void just_multiply(int a, int b)
{
    printf("Multiplied value=%d\n", a * b);
}

void just_leak()
{
    int * ptr1 = malloc(sizeof(int) * 15);
}
