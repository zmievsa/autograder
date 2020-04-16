public class TestResult {
    public static void main(String[] args) {
        int res = Homework.numberSaver();
        if (res == 54)
            TestHelper.PASS();
        else if (res == 83)
            TestHelper.RESULT(83);
        else
            TestHelper.FAIL();
    }
}