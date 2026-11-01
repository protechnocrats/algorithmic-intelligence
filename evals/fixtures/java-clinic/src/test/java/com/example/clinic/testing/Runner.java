package com.example.clinic.testing;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.Arrays;
import java.util.Comparator;

/** Minimal test runner: runs every @Test method of the named classes. */
public final class Runner {
    public static void main(String[] args) throws Exception {
        int passed = 0, failed = 0;
        for (String name : args) {
            Class<?> type = Class.forName(name);
            Method[] methods = type.getDeclaredMethods();
            Arrays.sort(methods, Comparator.comparing(Method::getName));
            for (Method m : methods) {
                if (!m.isAnnotationPresent(Test.class)) continue;
                Object instance = type.getDeclaredConstructor().newInstance();
                try {
                    m.invoke(instance);
                    passed++;
                } catch (InvocationTargetException e) {
                    failed++;
                    System.out.println("FAIL " + type.getSimpleName() + "." + m.getName() + ": " + e.getCause());
                }
            }
        }
        System.out.println(passed + " passed, " + failed + " failed");
        if (failed > 0) System.exit(1);
    }
}
