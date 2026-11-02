package com.example.clinic;

/** A sample waiting for the chemistry analyzer. Reagent use is in microliters; urgency is the triage score from the requesting ward. */
public record LabSample(long sampleId, long patientId, int reagentMicroliters, int urgency) {
    public LabSample {
        if (reagentMicroliters < 0) throw new IllegalArgumentException("reagent use cannot be negative");
    }
}
