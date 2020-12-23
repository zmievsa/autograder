// This class becomes the member class of the testcase, thus restricting
// the student from accessing helper array and helper methods
    private interface LibC extends Library {
        public int setenv(String name, String value, int overwrite);
        public int unsetenv(String name);
    }
    private static LibC libc = (LibC) Native.loadLibrary("c", LibC.class);

    private static int unsetenv(String name) {
        getenv().remove(name);
        return libc.unsetenv(name);
    }

    @SuppressWarnings("unchecked")
    private static Map<String, String> getenv() {
        try {
            Map<String, String> unmodifiableEnv = System.getenv();
            Class<?> cu = unmodifiableEnv.getClass();
            Field m = cu.getDeclaredField("m");
            m.setAccessible(true);
            return (Map<String, String>)m.get(unmodifiableEnv);
        }
        catch (Exception ex2) {
        }
        return new HashMap<String, String>();
    }


    private static String VALIDATING_STRING = ENABLE_ANTI_CHEAT();
    private static String ENABLE_ANTI_CHEAT() {
        String val = System.getenv("VALIDATING_STRING");
        unsetenv("VALIDATING_STRING");
        return val;
    }
    private static void CHECK_OUTPUT() {
        System.out.print("\n" + VALIDATING_STRING);
        System.exit({% CHECK_OUTPUT_EXIT_CODE %});
    }
    private static void RESULT(int result) {
        System.out.print("\n" + VALIDATING_STRING);
        System.exit(result + { % RESULT_EXIT_CODE_OFFSET % });
    }
    private static void PASS() {
        RESULT(100);
    }
    private static void FAIL() {
        RESULT(0);
    }