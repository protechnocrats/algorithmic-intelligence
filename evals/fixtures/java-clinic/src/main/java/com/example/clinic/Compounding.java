package com.example.clinic;

/** The pharmacy's compounding bench. */
public final class Compounding {
    private Compounding() {}

    /**
     * The number of ways an order can be filled from exactly three different vials on the shelf: unordered
     * triples of distinct vials whose contents add up to the ordered dose. Contents and doses are in micrograms.
     */
    public static long threeVialFills(int[] vialMicrograms, long doseMicrograms) {
        long count = 0;
        int n = vialMicrograms.length;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                for (int k = j + 1; k < n; k++) {
                    if ((long) vialMicrograms[i] + vialMicrograms[j] + vialMicrograms[k] == doseMicrograms) count++;
                }
            }
        }
        return count;
    }
}
