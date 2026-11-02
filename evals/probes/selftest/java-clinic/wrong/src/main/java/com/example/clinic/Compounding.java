package com.example.clinic;

import java.util.Arrays;

/** Wrong: sorts the caller's array in place, and adds in int, which overflows for large vials. */
public final class Compounding {
    private Compounding() {}

    public static long threeVialFills(int[] vialMicrograms, long doseMicrograms) {
        Arrays.sort(vialMicrograms);
        long count = 0;
        int n = vialMicrograms.length;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                for (int k = j + 1; k < n; k++) {
                    int sum = vialMicrograms[i] + vialMicrograms[j] + vialMicrograms[k];
                    if (sum == doseMicrograms) count++;
                }
            }
        }
        return count;
    }
}
