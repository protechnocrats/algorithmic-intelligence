package com.example.clinic;

import java.util.Arrays;

/** Wrong: Arrays.equals stops at the first differing byte, so the time reveals how much of a forged signature is right. */
public final class LabCallbacks {
    private LabCallbacks() {}

    public static boolean signatureMatches(byte[] computed, byte[] received) {
        return received != null && Arrays.equals(computed, received);
    }
}
