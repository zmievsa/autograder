// All public functions in student's file(s) are provided by autograder and can be used freely if you prototype them below.
// PASS(), RESULT(res), FAIL(), and CHECK_STDOUT() are also provided by autograder

public class TestResult {
    public static void main(String[] args) {
        int res = Homework.numberSaver(); // You can call any function from student's file like this
        if (res == 54)
            PASS();
        else
            FAIL();
    }
}