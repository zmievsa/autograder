// This class becomes the member class of the testcase, thus restricting
// the student from accessing helper array and helper methods
private static class TestHelper {
    private static int RESULT_EXIT_CODES[] = new int[] {{% RESULT_EXIT_CODES %}};
    public static void CHECK_OUTPUT() {
        System.exit({% CHECK_OUTPUT_EXIT_CODE %});
    }
    public static void RESULT(int result) {
        System.exit(RESULT_EXIT_CODES[result]);
    }
    
    public static void PASS() {
        RESULT(100);
    }
    public static void FAIL() {
        RESULT(0);
    }
}
