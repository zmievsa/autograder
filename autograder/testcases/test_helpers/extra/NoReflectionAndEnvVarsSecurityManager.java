// I included this file for reference only. It is not necessary for any functions in autograder
import java.lang.SecurityManager;

import java.lang.RuntimePermission;

import java.security.AccessController;
import java.security.Permission;
import java.lang.SecurityException;
import java.io.FileWriter;
import java.io.IOException;
import java.io.BufferedWriter;
import java.util.concurrent.TimeUnit;
import java.lang.ClassLoader;
import java.lang.reflect.*;

public class NoReflectionAndEnvVarsSecurityManager extends SecurityManager {

        // What if the student uses a lib that uses reflection?
        // https://stackoverflow.com/questions/8703678/how-can-i-check-if-a-class-belongs-to-java-jdk
        static ClassLoader SYS_CLS_LOADER = "".getClass().getClassLoader();
        @Override
        public void checkPermission(Permission perm) {
            String permStr = perm.toString();
            Class classes[] = this.getClassContext();
            if (perm instanceof RuntimePermission) {
                if (permStr.contains("getenv.VALIDATING_STRING") && classes[2].getClassLoader() != SYS_CLS_LOADER)
                    throw new SecurityException("Using environ is not permitted. It could indicate cheating.");
            }
            else if (perm instanceof ReflectPermission && classes[2].getClassLoader() != SYS_CLS_LOADER) {
                throw new SecurityException("Using reflection is not permitted. It could indicate cheating.");
            }
        }
        @Override
        public void checkPermission(Permission perm, Object context) {}
}
