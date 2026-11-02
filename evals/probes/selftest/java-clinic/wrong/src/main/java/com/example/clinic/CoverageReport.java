package com.example.clinic;

import java.time.LocalDate;
import java.util.*;

public final class CoverageReport {
    private final Availability availability;
    public CoverageReport(Availability availability) { this.availability = availability; }
    public List<LocalDate> uncoveredDays(List<Long> doctorIds, LocalDate from, LocalDate to, int minDoctors) {
        List<LocalDate> days = new ArrayList<>();
        Map<LocalDate, Integer> count = new HashMap<>();
        for (long doc : doctorIds) for (LocalDate d : availability.rosteredDays(doc, from, to)) count.merge(d, 1, Integer::sum);
        for (LocalDate d = from; !d.isAfter(to); d = d.plusDays(1)) if (count.getOrDefault(d, 0) < minDoctors) days.add(d);
        return days;
    }
}
