class TestHelper {
    public static void CHECK_OUTPUT() {
        System.exit({% CHECK_OUTPUT_EXIT_CODE %});
    }
    public static void RESULT(int result) {
        System.exit(result + ({% RESULT_EXIT_CODE_SHIFT %}));
    }
    
    public static void PASS() {
        System.exit({% MAX_RESULT %});
    }
    public static void FAIL() {
        System.exit({% MIN_RESULT %});
    }
}
