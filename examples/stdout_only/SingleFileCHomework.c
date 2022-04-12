#include <stdio.h>

int numberSaver()
{
    int arr[9] = {0};
    int userInput;
    int sum = 0;
    while (1)
    {
        printf("Input num from 1 to 9 (0 to exit):\n");
        scanf("%d", &userInput);
        if (userInput > 0 && userInput < 10)
            arr[userInput - 1]++;
        else
            break;
    }

    printf("You typed:\n");

    for (int i = 1; i < 10; i++)
    {
        printf("%d) %d time(s)\n", i, arr[i - 1]);
        sum += (arr[i - 1] * i);
    }

    return sum;
}

int main()
{
    numberSaver();
    return 0;
}
