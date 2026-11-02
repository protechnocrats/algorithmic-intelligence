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
        java.util.Map<VisitKey, Integer> counts = new java.util.LinkedHashMap<>();
        for (VisitKey v : upload) counts.merge(v, 1, Integer::sum);
        List<VisitKey> repeated = new ArrayList<>();
        counts.forEach((k, c) -> { if (c > 1) repeated.add(k); });
        return repeated;
    }
}
