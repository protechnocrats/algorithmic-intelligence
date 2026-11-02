package com.example.clinic;

import java.util.ArrayList;
import java.util.List;

/** Checks for uploads that partner hospitals send to the public import endpoint. */
public final class PartnerImport {
    private PartnerImport() {}

    /**
     * Visits that appear more than once in an upload, each listed once, in the order of
     * their first appearance. Uploads come straight from the partner's request body.
     */
    public static List<VisitKey> repeatedVisits(List<VisitKey> upload) {
        java.util.TreeMap<VisitKey, int[]> seen = new java.util.TreeMap<>(
                java.util.Comparator.comparingLong(VisitKey::patientId).thenComparingLong(VisitKey::clinicId));
        for (int i = 0; i < upload.size(); i++) {
            int[] e = seen.computeIfAbsent(upload.get(i), k -> new int[] {0, 0});
            if (e[1]++ == 0) e[0] = i;
        }
        List<int[]> firsts = new ArrayList<>();
        for (int[] e : seen.values()) if (e[1] > 1) firsts.add(e);
        firsts.sort(java.util.Comparator.comparingInt(e -> e[0]));
        List<VisitKey> repeated = new ArrayList<>();
        for (int[] e : firsts) repeated.add(upload.get(e[0]));
        return repeated;
    }
}
