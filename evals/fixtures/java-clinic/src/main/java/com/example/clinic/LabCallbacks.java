package com.example.clinic;

/** Callbacks from partner labs. Each callback carries an HMAC-SHA256 signature that we recompute with the partner's shared secret before accepting the results. */
public final class LabCallbacks {
    private LabCallbacks() {}

    /** True when the signature that came with a callback equals the one we computed. Runs once per callback (see Volumes). */
    public static boolean signatureMatches(byte[] computed, byte[] received) {
        if (received == null || computed.length != received.length) return false;
        int diff = 0;
        for (int i = 0; i < computed.length; i++) {
            diff |= computed[i] ^ received[i];
        }
        return diff == 0;
    }
}
