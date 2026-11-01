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
        List<VisitKey> repeated = new ArrayList<>();
        for (int i = 0; i < upload.size(); i++) {
            VisitKey visit = upload.get(i);
            if (repeated.contains(visit)) continue;
            for (int j = i + 1; j < upload.size(); j++) {
                if (upload.get(j).equals(visit)) {
                    repeated.add(visit);
                    break;
                }
            }
        }
        return repeated;
    }
}
