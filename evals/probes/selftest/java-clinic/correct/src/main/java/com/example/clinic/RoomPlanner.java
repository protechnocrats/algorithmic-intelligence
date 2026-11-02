package com.example.clinic;

import java.util.List;

/** Room planning for outpatient departments. */
public final class RoomPlanner {
    static final int MINUTES_PER_WEEK = 7 * 24 * 60;

    private RoomPlanner() {}

    /**
     * The fewest consulting rooms that can hold the day's appointments, with no two
     * appointments that overlap in time sharing a room.
     *
     * @throws IllegalArgumentException for an appointment that does not end after it starts
     */
    public static int roomsNeeded(List<Appointment> appointments) {
        for (Appointment a : appointments) {
            if (a.end() <= a.start()) {
                throw new IllegalArgumentException("appointment " + a.id() + " does not end after it starts");
            }
        }
        int[][] ev = new int[appointments.size() * 2][];
        int k = 0;
        for (Appointment a : appointments) { ev[k++] = new int[] {a.start(), 1}; ev[k++] = new int[] {a.end(), -1}; }
        java.util.Arrays.sort(ev, (p, q) -> p[0] != q[0] ? Integer.compare(p[0], q[0]) : Integer.compare(p[1], q[1]));
        int depth = 0, best = 0;
        for (int[] e : ev) { depth += e[1]; best = Math.max(best, depth); }
        return best;
    }

    /**
     * The fewest rooms that can hold a clinic's recurring weekly slots, with no two
     * slots that overlap in the week sharing a room.
     *
     * @throws IllegalArgumentException for a start outside the week or a length outside 1 to one week
     */
    public static int weeklyRoomsNeeded(List<WeeklySlot> slots) {
        for (WeeklySlot s : slots) {
            if (s.start() < 0 || s.start() >= MINUTES_PER_WEEK || s.length() < 1 || s.length() > MINUTES_PER_WEEK) {
                throw new IllegalArgumentException("slot " + s.id() + " is outside the week");
            }
        }
        int n = slots.size();
        boolean[][] conflict = new boolean[n][n];
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                WeeklySlot a = slots.get(i), b = slots.get(j);
                conflict[i][j] = i != j
                        && (Math.floorMod(b.start() - a.start(), MINUTES_PER_WEEK) < a.length()
                            || Math.floorMod(a.start() - b.start(), MINUTES_PER_WEEK) < b.length());
            }
        }
        return fewestRooms(conflict);
    }

    /** Tries 1, 2, 3, ... rooms until every item can be given a room. */
    private static int fewestRooms(boolean[][] conflict) {
        int n = conflict.length;
        for (int rooms = 1; rooms <= n; rooms++) {
            int[] room = new int[n];
            if (assign(0, rooms, room, conflict)) return rooms;
        }
        return 0;
    }

    private static boolean assign(int i, int rooms, int[] room, boolean[][] conflict) {
        if (i == conflict.length) return true;
        for (int r = 0; r < rooms; r++) {
            boolean free = true;
            for (int j = 0; j < i && free; j++) {
                if (conflict[i][j] && room[j] == r) free = false;
            }
            if (free) {
                room[i] = r;
                if (assign(i + 1, rooms, room, conflict)) return true;
            }
        }
        return false;
    }
}
