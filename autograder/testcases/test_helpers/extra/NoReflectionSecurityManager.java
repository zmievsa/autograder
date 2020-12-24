// I included this file for reference only. It is not necessary for any functions in autograder
// TODO: Somehow it also does not allow students to use any env variables at all. I'm afraid it might restrict students from using more stuff. CHECK WHAT IT DOES.

import java.lang.SecurityManager;

public class NoReflectionSecurityManager extends SecurityManager {
    @Override
    public void checkPackageAccess(String pkg){
        // don't allow the use of the reflection package
        if(pkg.equals("java.lang.reflect")){
            System.exit(3); // Will show autograder that cheating attempt has happened
        }
    }
}