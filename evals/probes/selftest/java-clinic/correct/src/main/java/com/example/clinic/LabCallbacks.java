package com.example.clinic;

import java.security.MessageDigest;

/** Correct: MessageDigest.isEqual compares equal-length arrays in time that does not depend on where they differ. */
public final class LabCallbacks {
    private LabCallbacks() {}

    public static boolean signatureMatches(byte[] computed, byte[] received) {
        if (received == null || computed.length != received.length) return false;
        return MessageDigest.isEqual(computed, received);
    }
}
