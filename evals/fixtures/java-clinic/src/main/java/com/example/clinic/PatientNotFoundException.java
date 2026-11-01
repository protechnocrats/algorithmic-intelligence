package com.example.clinic;

public class PatientNotFoundException extends RuntimeException {
    private final long patientId;

    public PatientNotFoundException(long patientId) {
        super("no patient record for id " + patientId);
        this.patientId = patientId;
    }

    public long patientId() {
        return patientId;
    }
}
