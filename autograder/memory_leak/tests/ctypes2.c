#include <stdio.h>
  
// Header file containing character functions
#include <ctype.h>
  
char* identify_convert_ul(char a[])
{
    int count_upper = 0, count_lower = 0;
    for (int i = 0; a[i] != '\0'; i++) {
  
        // To check the uppercase characters
        if (isupper(a[i])) {
            count_upper++;
            a[i] = tolower(a[i]);
        }
  
        // To check the lowercase characters
        else if (islower(a[i])) {
            count_lower++;
            a[i] = toupper(a[i]);
        }
    }
    printf("No. of uppercase characters are %d\n",
           count_upper);
    printf("No. of lowercase characters are %d",
           count_lower);
    return a;
}
  
int main()
{
    // String Initialization
    char a[] = "Hi, Welcome to GeeksForGeeks";
    char* p;
    p = identify_convert_ul(a);
    printf("%s", p);
}
