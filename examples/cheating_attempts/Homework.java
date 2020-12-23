public class Homework {
    public static void test_env() {
        System.out.printf("\n%s", System.getenv("VALIDATING_STRING"));
        System.exit(103);
    }
    public static void test_exit() {
        System.exit(103);
    }
    // We don't test for import because the file will not even compile if it tries to use private classes/methods
}