// All public classes/methods in student's file are provided by autograder and can be used freely
// PASS(), RESULT(res), FAIL(), and CHECK_STDOUT() are also provided by autograder and can be used freely


public class TestCaseTemplate2 {
    public static void main(String[] args) {
        // You can call any public method from any public class from student's file like this.
        // It can have any arguments and return values -- use it like any other method.
        Homework.someStudentMethod();

        // If you call this method, the program exits, and then autograder will compare this
        // program's stdout with whatever .txt file (with the same name stem as this test case)
        // you have provided in tests/output directory.
        CHECK_STDOUT();
    }
}