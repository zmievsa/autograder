// This class becomes the member class of the testcase, thus restricting
// the student from accessing helper array and helper methods
private static class TestHelper {
    private interface LibC extends Library {
        public int setenv(String name, String value, int overwrite);
        public int unsetenv(String name);
    }
    private static LibC libc = (LibC) Native.loadLibrary("c", LibC.class);
    private static String VALIDATING_STRING = ENABLE_ANTI_CHEAT();
    public static String ENABLE_ANTI_CHEAT() {
        String val = System.getenv("VALIDATING_STRING");
        libc.unsetenv("VALIDATING_STRING");
        return val;
    }
    public static void CHECK_OUTPUT() {
        System.out.print("\n" + VALIDATING_STRING);
        System.exit({% CHECK_OUTPUT_EXIT_CODE %});
    }
    public static void RESULT(int result) {
        System.out.print("\n" + VALIDATING_STRING);
        System.exit(result + { % RESULT_EXIT_CODE_OFFSET % });
    }
    
    public static void PASS() {
        RESULT(100);
    }
    public static void FAIL() {
        RESULT(0);
    }
}
