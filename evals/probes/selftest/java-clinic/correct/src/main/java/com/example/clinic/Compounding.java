package com.example.clinic;

import java.util.HashMap;
import java.util.Map;

/** Correct: for each first vial, scan the third while counting the middle values seen, O(n^2) expected; sums in long; the input is not changed. */
public final class Compounding {
    private Compounding() {}

    public static long threeVialFills(int[] vialMicrograms, long doseMicrograms) {
        long count = 0;
        int n = vialMicrograms.length;
        for (int i = 0; i < n; i++) {
            Map<Long, Integer> middle = new HashMap<>();
            for (int k = i + 1; k < n; k++) {
                long need = doseMicrograms - vialMicrograms[i] - (long) vialMicrograms[k];
                count += middle.getOrDefault(need, 0);
                middle.merge((long) vialMicrograms[k], 1, Integer::sum);
            }
        }
        return count;
    }
}
