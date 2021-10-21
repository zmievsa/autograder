#include <stdio.h>
  
// Header file containing character functions
#include <ctype.h>
  
void identify_alpha_numeric(char a[])
{
    int count_alpha = 0, count_digit = 0;
    for (int i = 0; a[i] != '\0'; i++) {
        // To check the character is alphabet
        if (isalpha(a[i]))
            count_alpha++;
  
        // To check the character is a digit
        if (isdigit(a[i]))
            count_digit++;
    }
    printf("The number of alphabets are %d\n",
           count_alpha);
    printf("The number of digits are %d",
           count_digit);
}
  
int main()
{
    // String Initialization
    char a[]
        = "Hi 1234, "
          " Welcome to GeeksForGeeks";
    identify_alpha_numeric(a);
}
