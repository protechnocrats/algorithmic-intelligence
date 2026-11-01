package com.example.clinic;

/** Identifies one visit in a partner hospital's upload. */
public record VisitKey(long patientId, long clinicId) {}
