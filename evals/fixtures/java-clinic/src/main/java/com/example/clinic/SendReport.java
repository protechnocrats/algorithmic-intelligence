package com.example.clinic;

import java.util.List;

/** How many reminders were sent, and the ids of those the provider rejected, in send order. */
public record SendReport(int sent, List<Long> rejectedIds) {}
