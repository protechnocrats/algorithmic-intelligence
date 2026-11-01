package com.example.clinic;

/**
 * A slot that recurs every week. {@code start} is the minute of the week (0 is Monday
 * 00:00); the slot occupies {@code length} minutes from there and may run past
 * Sunday midnight into Monday.
 */
public record WeeklySlot(long id, int start, int length) {}
