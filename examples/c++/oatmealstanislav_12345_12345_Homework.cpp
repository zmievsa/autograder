#include <iostream>

using namespace std;

int numberSaver()
{
    int arr[9] = {0};
    int userInput;
    int sum = 0;
    while (1)
        {
            cout << "Input number from 1 to 9 (0 to exit):\n";
            cin >> userInput;
            if (userInput > 0 && userInput < 10)
                arr[userInput - 1]++;
            else
                break;
        }

    cout << "You typed:\n";

    for (int i = 1; i < 10; i++)
    {
        cout << i << ") " << arr[i - 1] << " time(s)\n";
        sum += (arr[i - 1] * i);
    }

    return sum;
}

int main() {
    numberSaver();
    cout << "Random stuff1\n";
    return 0;
}
