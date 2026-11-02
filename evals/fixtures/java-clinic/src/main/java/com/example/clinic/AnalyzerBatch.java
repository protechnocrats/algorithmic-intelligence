package com.example.clinic;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Plans the next run of the chemistry analyzer. */
public final class AnalyzerBatch {
    private AnalyzerBatch() {}

    /**
     * The highest total urgency of samples that fit in one run's reagent capacity. At most one sample per
     * patient goes into a run: the analyzer's carousel holds one tube per patient barcode.
     */
    public static long bestUrgency(List<LabSample> pending, int capacityMicroliters) {
        return best(pending, 0, capacityMicroliters, new HashSet<>());
    }

    private static long best(List<LabSample> pending, int i, int remaining, Set<Long> patientsInRun) {
        if (i == pending.size()) return 0;
        long skip = best(pending, i + 1, remaining, patientsInRun);
        LabSample s = pending.get(i);
        if (s.reagentMicroliters() > remaining || patientsInRun.contains(s.patientId())) return skip;
        patientsInRun.add(s.patientId());
        long take = s.urgency() + best(pending, i + 1, remaining - s.reagentMicroliters(), patientsInRun);
        patientsInRun.remove(s.patientId());
        return Math.max(skip, take);
    }
}
