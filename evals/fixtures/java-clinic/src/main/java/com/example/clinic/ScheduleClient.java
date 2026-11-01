package com.example.clinic;

import java.time.LocalDate;
import java.util.Set;

/** The rostering system. One round trip per call (about 5 ms). */
public interface ScheduleClient {
    /** The days in [from, to] on which the doctor is rostered. */
    Set<LocalDate> rosteredDays(long doctorId, LocalDate from, LocalDate to);
}
