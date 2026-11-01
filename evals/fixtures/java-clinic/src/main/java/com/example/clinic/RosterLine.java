package com.example.clinic;

public record RosterLine(long appointmentId, String time, String patientName, String ward) {}
