package com.example.clinic;

/** An appointment on one day. Times are minutes after midnight; the end is exclusive. */
public record Appointment(long id, long patientId, int start, int end) {}
