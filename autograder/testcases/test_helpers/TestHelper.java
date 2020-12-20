// This class becomes the member class of the testcase, thus restricting
// the student from accessing helper array and helper methods
private static class TestHelper {
    public static void CHECK_OUTPUT() {
        System.out.print("\n{ % VALIDATING_STRING % }");
        System.exit({% CHECK_OUTPUT_EXIT_CODE %});
    }
    public static void RESULT(int result) {
        System.out.print("\n{ % VALIDATING_STRING % }");
        System.exit(result + { % RESULT_EXIT_CODE_OFFSET % });
    }
    
    public static void PASS() {
        RESULT(100);
    }
    public static void FAIL() {
        RESULT(0);
    }
}
