class TestHelper {
    public static void NO_RESULT() {
        System.exit(%d);             // RESULTLESS_EXIT_CODE
    }
    public static void RESULT(int result) {
        System.exit(result + (%d));  // RESULT_EXIT_CODE_SHIFT
    }
    
    public static void PASS() {
        System.exit(%d);            // MIN_RESULT
    }
    public static void FAIL() {
        System.exit(%d);            // MAX_RESULT
    }
}
