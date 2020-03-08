public class TestHelper {
    public static void NO_RESULT() {
        System.exit(0);
    }
    public static void RESULT(int result) {
        System.exit(result + 3);
    }
    
    public static void PASS() {
        RESULT(100);
    }
    public static void FAIL() {
        RESULT(0);
    }
}