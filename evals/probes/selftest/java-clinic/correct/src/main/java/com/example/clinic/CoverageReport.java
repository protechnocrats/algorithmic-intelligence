package com.example.clinic;

import java.time.LocalDate;
import java.util.*;

public final class CoverageReport {
    private final Availability availability;
    public CoverageReport(Availability availability) { this.availability = availability; }
    public List<LocalDate> uncoveredDays(List<Long> doctorIds, LocalDate from, LocalDate to, int minDoctors) {
        List<LocalDate> days = new ArrayList<>();
        for (LocalDate d = from; !d.isAfter(to); d = d.plusDays(1)) {
            int n = 0;
            for (long doc : doctorIds) if (availability.isAvailable(doc, d)) n++;
            if (n < minDoctors) days.add(d);
        }
        return days;
    }
}
