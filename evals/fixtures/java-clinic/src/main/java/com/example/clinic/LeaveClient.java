package com.example.clinic;

import java.time.LocalDate;
import java.util.Set;

/** The HR leave system. One round trip per call (about 5 ms). */
public interface LeaveClient {
    /** The days in [from, to] on which the doctor is on approved leave. */
    Set<LocalDate> leaveDays(long doctorId, LocalDate from, LocalDate to);
}
