// This class becomes the member class of the testcase, thus restricting
// the student from accessing helper array and helper methods
// https://blog.quirk.es/2009/11/setting-environment-variables-in-java.html
    private interface LibC extends Library {
        public int {% SETENV %}(String name);
    }

    private static int setenv(String name) {
        getenv().remove(name);
        try {
            LibC libc = (LibC) Native.loadLibrary("{% C_LIBRARY %}", LibC.class);
            return libc.{% SETENV %}(name + "=NULL");
        } catch (Throwable e) {
            // Java.io.Exception that happens if mscvrt is unavailable in Windows
            // Usually it is the case when you run autograder without admin rights
            return 0;
        }
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
        setenv("VALIDATING_STRING");
        return val;
    }
    private static void CHECK_STDOUT() {
        System.out.printf("\n-1{% SPLITCHAR %}%s", VALIDATING_STRING);
        System.exit({% CHECK_STDOUT_EXIT_CODE %});
    }
    private static void RESULT(double r) {
        System.out.printf("\n%f{% SPLITCHAR %}%s", r, VALIDATING_STRING);
        System.exit({ % RESULT_EXIT_CODE % });
    }
    private static void PASS() {
        RESULT(100);
    }
    private static void FAIL() {
        RESULT(0);
    }