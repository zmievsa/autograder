import java.util.Scanner;

public class Homework {
    public static void main(String[] args) {
        numberSaver();
    }
    public static int numberSaver() {
        int arr[] = new int[9];
        int sum = 0;
        int userInput;
        Scanner sc = new Scanner(System.in);
        while (true)
        {
            System.out.println("Input number from 1 to 9 (0 to exit):");
            userInput = sc.nextInt();
            if (userInput > 0 && userInput < 10)
                arr[userInput - 1]++;
            else
                break;
        }

        System.out.println("You typed:");

        for (int i = 1; i < 10; i++)
        {
            System.out.printf("%d) %d time(s)\n", i, arr[i - 1]);
            sum += (arr[i - 1] * i);
        }

        return sum;
    }
}