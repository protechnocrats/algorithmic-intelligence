package com.example.clinic;

/**
 * An opening session of a clinic, in minutes of the week (0 is Monday 00:00). Both
 * ends are inclusive. A session whose end is before its start runs past Sunday
 * midnight into Monday.
 */
public record Session(String name, int first, int last) {
    boolean contains(int minuteOfWeek) {
        return first <= last
                ? minuteOfWeek >= first && minuteOfWeek <= last
                : minuteOfWeek >= first || minuteOfWeek <= last;
    }
}
