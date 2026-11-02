package com.example.clinic;

import java.util.List;

/** Wrong: plain 0/1 knapsack. It ignores the one-sample-per-patient rule, so it can put two of a patient's samples in one run. */
public final class AnalyzerBatch {
    private AnalyzerBatch() {}

    public static long bestUrgency(List<LabSample> pending, int capacityMicroliters) {
        if (capacityMicroliters < 0) return 0;
        long[] best = new long[capacityMicroliters + 1];
        for (LabSample s : pending) {
            for (int c = capacityMicroliters; c >= s.reagentMicroliters(); c--) {
                best[c] = Math.max(best[c], best[c - s.reagentMicroliters()] + s.urgency());
            }
        }
        return best[capacityMicroliters];
    }
}
