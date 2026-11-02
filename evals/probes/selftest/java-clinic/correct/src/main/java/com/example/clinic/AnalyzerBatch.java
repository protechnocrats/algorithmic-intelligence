package com.example.clinic;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Correct: knapsack with one choice per patient group, O(n * capacity), capacity iterated downward against the previous groups' table. */
public final class AnalyzerBatch {
    private AnalyzerBatch() {}

    public static long bestUrgency(List<LabSample> pending, int capacityMicroliters) {
        if (capacityMicroliters < 0) return 0;
        Map<Long, List<LabSample>> byPatient = new LinkedHashMap<>();
        for (LabSample s : pending) byPatient.computeIfAbsent(s.patientId(), k -> new ArrayList<>()).add(s);
        long[] best = new long[capacityMicroliters + 1];
        for (List<LabSample> group : byPatient.values()) {
            long[] next = best.clone();
            for (LabSample s : group) {
                for (int c = capacityMicroliters; c >= s.reagentMicroliters(); c--) {
                    next[c] = Math.max(next[c], best[c - s.reagentMicroliters()] + s.urgency());
                }
            }
            best = next;
        }
        return best[capacityMicroliters];
    }
}
