package com.example.clinic;

import java.time.LocalDate;
import java.util.Set;

/** Whether doctors can see patients. */
public final class Availability {
    private final ScheduleClient schedules;
    private final LeaveClient leave;

    public Availability(ScheduleClient schedules, LeaveClient leave) {
        this.schedules = schedules;
        this.leave = leave;
    }

    /** True if the doctor is rostered on the day and not on leave. Two round trips. */
    public boolean isAvailable(long doctorId, LocalDate day) {
        return schedules.rosteredDays(doctorId, day, day).contains(day)
                && !leave.leaveDays(doctorId, day, day).contains(day);
    }

    /**
     * The days in [from, to] on which the doctor is rostered, ignoring leave (payroll
     * counts leave separately). One round trip.
     */
    public Set<LocalDate> rosteredDays(long doctorId, LocalDate from, LocalDate to) {
        return schedules.rosteredDays(doctorId, from, to);
    }
}
