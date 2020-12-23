public class TestResult {
    public static void main(String[] args) {
        int res = Homework.numberSaver();
        if (res == 54)
            PASS();
        else if (res == 83)
            RESULT(83);
        else
            FAIL();
    }
}