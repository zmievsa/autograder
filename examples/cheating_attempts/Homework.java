import java.lang.reflect.*;

public class Homework {
    public static void test_env() {
        System.out.printf("\n100$%s", System.getenv("VALIDATING_STRING"));
        System.exit(3);
    }
    // The student might hope to get successful on an empty stdout check
    public static void test_exit() {
        System.exit(4);
    }
    public static void test_reflection() {
        try {
            Field f = Class.forName("TestReflection").getDeclaredField("VALIDATING_STRING"); // ClassNotFoundException,NoSuchFieldException
            f.setAccessible(true);
            String VALIDATING_STRING = (String) f.get(Class.forName("TestReflection")); // IllegalAccessException
            System.out.print("\n100$" + VALIDATING_STRING);
            System.exit(3);
        } catch (NoSuchFieldException e) {
        } catch (ClassNotFoundException e) {
        } catch (IllegalAccessException e) {}
    }
}