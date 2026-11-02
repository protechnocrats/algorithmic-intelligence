package com.example.clinic;

import java.util.ArrayList;
import java.util.List;

/** A clinic's weekly opening sessions. */
public final class SessionCalendar {
    public static final int MINUTES_PER_WEEK = 7 * 24 * 60;

    private final List<Session> sessions;

    public SessionCalendar(List<Session> sessions) {
        for (Session s : sessions) {
            if (s.first() < 0 || s.first() >= MINUTES_PER_WEEK || s.last() < 0 || s.last() >= MINUTES_PER_WEEK) {
                throw new IllegalArgumentException("session " + s.name() + " is outside the week");
            }
        }
        this.sessions = List.copyOf(sessions);
    }

    /** The main outpatient clinic's sessions. */
    public static SessionCalendar outpatients() {
        List<Session> s = new ArrayList<>();
        String[] days = {"Mon", "Tue", "Wed", "Thu", "Fri"};
        for (int d = 0; d < 5; d++) {
            s.add(new Session(days[d] + " day", minute(d, 8, 0), minute(d, 17, 59)));
        }
        s.add(new Session("Mon evening", minute(0, 18, 0), minute(0, 20, 59)));
        s.add(new Session("Wed evening", minute(2, 18, 0), minute(2, 20, 59)));
        s.add(new Session("Fri late line", minute(4, 22, 0), minute(5, 1, 59)));
        s.add(new Session("Sat morning", minute(5, 9, 0), minute(5, 12, 59)));
        s.add(new Session("Sun on-call", minute(6, 18, 0), minute(6, 23, 50)));
        return new SessionCalendar(s);
    }

    private static int minute(int day, int hour, int minute) {
        return day * 24 * 60 + hour * 60 + minute;
    }

    /**
     * Minutes from {@code minuteOfWeek} until the clinic is next open: 0 if it is
     * open then, and -1 if it has no sessions. The week wraps from Sunday to Monday.
     *
     * @throws IllegalArgumentException if minuteOfWeek is outside 0 to 10079
     */
    public int minutesUntilOpen(int minuteOfWeek) {
        if (minuteOfWeek < 0 || minuteOfWeek >= MINUTES_PER_WEEK) {
            throw new IllegalArgumentException("minute of week out of range: " + minuteOfWeek);
        }
        return table()[minuteOfWeek];
    }

    private int[] table;

    private int[] table() {
        if (table != null) return table;
        int w = MINUTES_PER_WEEK;
        int[] t = new int[w];
        int next = -1;
        for (int pass = 0; pass < 2; pass++) {
            for (int m = w - 1; m >= 0; m--) {
                if (isOpen(m)) next = 0; else if (next >= 0) next++;
                t[m] = next;
            }
        }
        return table = t;
    }

    private boolean isOpen(int minuteOfWeek) {
        for (Session s : sessions) {
            if (s.contains(minuteOfWeek)) return true;
        }
        return false;
    }
}
