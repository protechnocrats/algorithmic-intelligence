import com.example.clinic.*;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.time.LocalDate;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

/**
 * Grading checks for java-clinic. Run by evals/probes/java-clinic.py, compiled
 * against a run's sources: java Probe <check>. Prints one result per line.
 */
public class Probe {
    static void out(Object o) { System.out.println(o); }

    static String outcome(Supplier<Object> body) {
        try {
            Object r = body.get();
            if (r instanceof double[] d) {
                StringBuilder b = new StringBuilder("ok [");
                for (double x : d) b.append(Double.toString(x)).append(' ');
                return b.append(']').toString();
            }
            return "ok " + r;
        } catch (PatientNotFoundException e) {
            return "raises PatientNotFoundException(" + e.patientId() + ")";
        } catch (RuntimeException e) {
            return "raises " + e.getClass().getSimpleName();
        }
    }

    public static void main(String[] args) throws Exception {
        switch (args[0]) {
            case "J1" -> j1();
            case "J1-trips" -> j1Trips();
            case "J2" -> j2();
            case "J2-memory" -> j2Memory();
            case "J2-time" -> j2Time();
            case "J3" -> j3();
            case "J3-rate" -> j3Rate();
            case "J4" -> j4();
            case "J5" -> j5();
            case "J5-time" -> j5Time();
            case "J6" -> j6();
            case "J7" -> j7();
            case "J8" -> j8();
            case "J9" -> j9();
            case "J9-time" -> j9Time();
            case "J10" -> j10();
            case "JW1" -> jw1();
            default -> throw new IllegalArgumentException(args[0]);
        }
    }

    // ---------- J1 ----------
    static final class Directory implements PatientDirectory {
        final Map<Long, Patient> records = new HashMap<>();
        int trips;
        Directory(int patients, Set<Long> missing) {
            for (long id = 1; id <= patients; id++) if (!missing.contains(id)) records.put(id, new Patient(id, "P" + id, "W" + id % 7));
        }
        public Patient fetch(long id) {
            trips++;
            Patient p = records.get(id);
            if (p == null) throw new PatientNotFoundException(id);
            return p;
        }
        public Map<Long, Patient> fetchAll(Collection<Long> ids) {
            if (ids.size() > 500) throw new IllegalArgumentException("more than 500 ids");
            trips++;
            Map<Long, Patient> m = new HashMap<>();
            for (long id : ids) if (records.containsKey(id)) m.put(id, records.get(id));
            return m;
        }
    }

    static List<Appointment> appointments(Random rng, int n, int patients) {
        List<Appointment> a = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            int s = 480 + rng.nextInt(600);
            a.add(new Appointment(1000 + i, 1 + rng.nextInt(patients), s, s + 20));
        }
        return a;
    }

    static void j1() {
        Random rng = new Random(1);
        List<Appointment> big = appointments(rng, 1200, 900);
        out(outcome(() -> new RosterService(new Directory(900, Set.of())).dailyRoster(big)));
        out(outcome(() -> new RosterService(new Directory(900, Set.of())).dailyRoster(List.of())));
        // Missing patients: the first missing one in appointment order is reported.
        List<Appointment> withMissing = new ArrayList<>(big);
        withMissing.add(700, new Appointment(1, 950, 600, 620));
        withMissing.add(300, new Appointment(2, 960, 600, 620));
        out(outcome(() -> new RosterService(new Directory(900, Set.of())).dailyRoster(withMissing)));
        out(outcome(() -> new RosterService(new Directory(900, Set.of(5L, 6L))).dailyRoster(
                List.of(new Appointment(1, 1, 500, 520), new Appointment(2, 6, 500, 520), new Appointment(3, 5, 500, 520)))));
    }

    static void j1Trips() {
        Directory d = new Directory(900, Set.of());
        new RosterService(d).dailyRoster(appointments(new Random(2), 2000, 900));
        out(d.trips + " round trips for 2,000 appointments");
    }

    // ---------- J2 ----------
    static List<Term> terminology(int n, String suffix) {
        List<Term> t = new ArrayList<>();
        for (int i = 0; i < n; i++) t.add(new Term("LAB " + (1000 + i) + "-" + (i % 10), "Test " + i + suffix));
        return t;
    }

    static void j2() {
        CodeFormatter f = new CodeFormatter(terminology(2000, ""));
        String[] raw = {" lab:1005 5 ", "Lab-1999-9", "LAB 1005-5", "lab1005-5", "lab 1005 5", "  ", "", "LAB 99999-1", "xyz", "LAB:01005-5",
                "lab:1005-55", "LAB 1005 -5", "ÅLAB 1005-5", "lab\t1005-5", "LAB 1005-5\n"};
        for (String r : raw) out(outcome(() -> f.label(r)));
        f.reload(terminology(2000, " (rev 2)"));
        for (String r : raw) out(outcome(() -> f.label(r)));
        f.reload(List.of(new Term("LAB 1005-5", "Only")));
        for (String r : raw) out(outcome(() -> f.label(r)));
        CodeFormatter dup = new CodeFormatter(List.of(new Term("LAB 7-1", "first"), new Term("LAB 7-1", "second")));
        out(outcome(() -> dup.label("lab 7 1")));
    }

    static void j2Memory() throws Exception {
        CodeFormatter f = new CodeFormatter(terminology(90_000, ""));
        Runtime rt = Runtime.getRuntime();
        for (int i = 0; i < 3; i++) { System.gc(); Thread.sleep(100); }
        long before = rt.totalMemory() - rt.freeMemory();
        for (int i = 0; i < 400_000; i++) f.label(" lab:" + (1000 + i % 90_000) + " " + (i % 10) + " #" + i);
        for (int i = 0; i < 3; i++) { System.gc(); Thread.sleep(100); }
        long after = rt.totalMemory() - rt.freeMemory();
        out(String.format("retained after one day's distinct raw codes: %.0f MB", (after - before) / 1e6) + " " + f.hashCode() % 1);
    }

    static void j2Time() {
        CodeFormatter f = new CodeFormatter(terminology(90_000, ""));
        Random rng = new Random(4);
        long t = System.nanoTime();
        for (int i = 0; i < 2000; i++) f.label("lab:" + (1000 + rng.nextInt(90_000)) + " " + rng.nextInt(10));
        out(String.format("%.1f us per label", (System.nanoTime() - t) / 2000 / 1000.0));
    }

    // ---------- J3 ----------
    static final class Gateway implements SmsGateway {
        final List<Long> delivered = new ArrayList<>();
        final List<Long> requestTimes = new ArrayList<>();
        final Set<Long> invalid;
        Gateway(Set<Long> invalid) { this.invalid = invalid; }
        synchronized void request() { requestTimes.add(System.nanoTime()); }
        public void send(Reminder r) {
            request();
            sleep(3);
            if (invalid.contains(r.id())) throw new GatewayException("rejected");
            synchronized (this) { delivered.add(r.id()); }
        }
        public void sendBatch(List<Reminder> rs) {
            if (rs.size() > 50) throw new IllegalArgumentException("more than 50");
            request();
            sleep(3);
            for (Reminder r : rs) if (invalid.contains(r.id())) throw new GatewayException("rejected");
            synchronized (this) { for (Reminder r : rs) delivered.add(r.id()); }
        }
        static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { throw new RuntimeException(e); } }
    }

    static List<Reminder> reminders(int n) {
        List<Reminder> r = new ArrayList<>();
        for (int i = 0; i < n; i++) r.add(new Reminder(i, "+1555" + i, "Reminder " + i));
        return r;
    }

    static void j3() {
        Gateway g = new Gateway(Set.of(7L, 8L, 60L, 149L));
        out(outcome(() -> new ReminderSender(g, 10).sendAll(reminders(150))));
        out("delivered in order: " + g.delivered);
        Gateway none = new Gateway(Set.of());
        out(outcome(() -> new ReminderSender(none, 10).sendAll(List.of())));
    }

    static void j3Rate() {
        Gateway g = new Gateway(Set.of(7L, 8L, 60L, 149L));
        new ReminderSender(g, 10).sendAll(reminders(150));
        List<Long> t = new ArrayList<>(g.requestTimes);
        Collections.sort(t);
        int worst = 0;
        for (int i = 0, j = 0; i < t.size(); i++) {
            while (t.get(i) - t.get(j) >= 100_000_000L) j++;
            worst = Math.max(worst, i - j + 1);
        }
        out((worst <= 10 ? "ok" : "RATE LIMIT EXCEEDED") + ": at most " + worst + " requests in any window of 10 pauses (limit 10); " + t.size() + " requests in all");
    }

    // ---------- J4 ----------
    static void j4() {
        AtomicInteger loads = new AtomicInteger();
        Map<Long, Chart> charts = new HashMap<>();
        for (long i = 1; i <= 5; i++) charts.put(i, new Chart(i, i, i == 4 ? List.of() : List.of("a" + i, "b" + i)));
        ChartRepository repo = new ChartRepository(id -> { loads.incrementAndGet(); return charts.get(id); });
        out(outcome(() -> ChartViewer.latestEntries(repo, List.of(1L, 2L, 1L, 4L, 3L, 2L, 1L, 4L))));
        out(outcome(() -> ChartViewer.latestEntries(repo, List.of(9L))));
        out("store loads: " + loads.get());
    }

    // ---------- J5 / J6 ----------
    static void j5() {
        Random rng = new Random(11);
        StringBuilder all = new StringBuilder();
        for (int t = 0; t < 1500; t++) {
            int n = rng.nextInt(12);
            List<Appointment> ap = new ArrayList<>();
            for (int i = 0; i < n; i++) {
                int s = rng.nextInt(12) * 15;
                ap.add(new Appointment(i, i, s, s + 15 * (1 + rng.nextInt(4))));
            }
            all.append(outcome(() -> RoomPlanner.roomsNeeded(ap))).append(t % 50 == 49 ? "\n" : " ");
        }
        out(all.toString().strip());
        out(outcome(() -> RoomPlanner.roomsNeeded(List.of(new Appointment(1, 1, 60, 120), new Appointment(2, 1, 600, 590)))));
        out(outcome(() -> RoomPlanner.roomsNeeded(List.of(new Appointment(1, 1, 60, 60)))));
        out(outcome(() -> RoomPlanner.roomsNeeded(List.of(new Appointment(1, 1, -30, 60), new Appointment(2, 1, 0, 30)))));
    }

    static void j5Time() {
        Random rng = new Random(5);
        List<Appointment> ap = new ArrayList<>();
        for (int i = 0; i < 400; i++) {
            int s = 480 + rng.nextInt(600);
            ap.add(new Appointment(i, i, s, s + 15 + rng.nextInt(46)));
        }
        long t = System.nanoTime();
        int rooms = RoomPlanner.roomsNeeded(ap);
        out(String.format("400 appointments: %d rooms in %.1f ms", rooms, (System.nanoTime() - t) / 1e6));
    }

    static void j6() {
        int w = 10080;
        // An odd cycle of five arcs: never more than two overlap at once, but three rooms are needed.
        List<WeeklySlot> cycle = new ArrayList<>();
        for (int i = 0; i < 5; i++) cycle.add(new WeeklySlot(i, i * 2016, 2400));
        out(outcome(() -> RoomPlanner.weeklyRoomsNeeded(cycle)));
        List<WeeklySlot> cycle7 = new ArrayList<>();
        for (int i = 0; i < 7; i++) cycle7.add(new WeeklySlot(i, i * 1440, 1700));
        out(outcome(() -> RoomPlanner.weeklyRoomsNeeded(cycle7)));
        Random rng = new Random(12);
        StringBuilder all = new StringBuilder();
        for (int t = 0; t < 3000; t++) {
            int n = 1 + rng.nextInt(10);
            List<WeeklySlot> s = new ArrayList<>();
            for (int i = 0; i < n; i++) s.add(new WeeklySlot(i, rng.nextInt(14) * 720, 720 * (1 + rng.nextInt(5))));
            all.append(outcome(() -> RoomPlanner.weeklyRoomsNeeded(s))).append(t % 50 == 49 ? "\n" : " ");
        }
        out(all.toString().strip());
        out(outcome(() -> RoomPlanner.weeklyRoomsNeeded(List.of(new WeeklySlot(1, 0, w), new WeeklySlot(2, 5000, 1)))));
        out(outcome(() -> RoomPlanner.weeklyRoomsNeeded(List.of(new WeeklySlot(1, w - 1, 2), new WeeklySlot(2, 0, 1)))));
        out(outcome(() -> RoomPlanner.weeklyRoomsNeeded(List.of(new WeeklySlot(1, w, 10)))));
        out(outcome(() -> RoomPlanner.weeklyRoomsNeeded(List.of(new WeeklySlot(1, 0, 0)))));
        out(outcome(() -> RoomPlanner.weeklyRoomsNeeded(List.of(new WeeklySlot(1, 0, w + 1)))));
        out(outcome(() -> RoomPlanner.weeklyRoomsNeeded(List.of())));
    }

    // ---------- J7 ----------
    static void j7() {
        int w = SessionCalendar.MINUTES_PER_WEEK;
        List<SessionCalendar> calendars = new ArrayList<>();
        calendars.add(SessionCalendar.outpatients());
        calendars.add(new SessionCalendar(List.of()));
        calendars.add(new SessionCalendar(List.of(new Session("wrap", w - 30, 29))));
        calendars.add(new SessionCalendar(List.of(new Session("one minute", 5000, 5000))));
        calendars.add(new SessionCalendar(List.of(new Session("last minute", w - 1, w - 1))));
        calendars.add(new SessionCalendar(List.of(new Session("whole week", 0, w - 1))));
        Random rng = new Random(13);
        for (int c = 0; c < 6; c++) {
            List<Session> s = new ArrayList<>();
            for (int i = 0, k = 1 + rng.nextInt(4); i < k; i++) s.add(new Session("s" + i, rng.nextInt(w), rng.nextInt(w)));
            calendars.add(new SessionCalendar(s));
        }
        for (SessionCalendar cal : calendars) {
            StringBuilder line = new StringBuilder();
            for (int m = 0; m < w; m++) line.append(cal.minutesUntilOpen(m)).append(' ');
            out(line.toString().strip());
            out(outcome(() -> cal.minutesUntilOpen(-1)) + " " + outcome(() -> cal.minutesUntilOpen(w)) + " " + outcome(() -> cal.minutesUntilOpen(Integer.MIN_VALUE)));
        }
    }

    // ---------- J8 ----------
    static void j8() {
        Random rng = new Random(8);
        int n = 20_000;
        double[] amounts = new double[n];
        for (int i = 0; i < n; i++) amounts[i] = Math.round((rng.nextDouble() * 400 - 150) * 100) / 100.0;
        amounts[17] = -0.0;
        List<Range> ranges = new ArrayList<>();
        for (int i = 0; i < 400; i++) {
            int from = (rng.nextInt(24) * n) / 24;
            ranges.add(new Range(from, from + rng.nextInt(n - from + 1)));
        }
        ranges.add(new Range(17, 18));
        ranges.add(new Range(5, 5));
        ranges.add(new Range(0, n));
        out(outcome(() -> Ledger.rangeTotals(amounts, ranges)));
        out(outcome(() -> Ledger.rangeTotals(amounts, List.of(new Range(10, 9)))));
        out(outcome(() -> Ledger.rangeTotals(amounts, List.of(new Range(0, 1), new Range(-1, 3)))));
        out(outcome(() -> Ledger.rangeTotals(new double[] {Double.NaN, 1, Double.POSITIVE_INFINITY, -1e308, -1e308}, List.of(new Range(0, 2), new Range(1, 3), new Range(3, 5), new Range(2, 5)))));
        out(outcome(() -> Ledger.rangeTotals(new double[] {1e16, 1, -1e16, 1}, List.of(new Range(0, 4), new Range(1, 4), new Range(0, 2)))));
    }

    // ---------- J9 ----------
    static void j9() {
        Random rng = new Random(9);
        for (int t = 0; t < 200; t++) {
            List<VisitKey> up = new ArrayList<>();
            for (int i = 0, n = rng.nextInt(40); i < n; i++) up.add(new VisitKey(rng.nextInt(6), rng.nextInt(3)));
            out(outcome(() -> PartnerImport.repeatedVisits(up)));
        }
        out(outcome(() -> PartnerImport.repeatedVisits(List.of())));
    }

    static void j9Time() {
        // Every key has the same hashCode on OpenJDK (record hash 31 * h(patientId) + h(clinicId)).
        List<VisitKey> up = new ArrayList<>();
        for (int i = 0; i < 40_000; i++) up.add(new VisitKey(i, (-31L * i) & 0xFFFFFFFFL));
        for (int i = 0; i < 40_000; i += 2) up.add(new VisitKey(i, (-31L * i) & 0xFFFFFFFFL));
        long t = System.nanoTime();
        int r = PartnerImport.repeatedVisits(up).size();
        out(String.format("60,000 colliding rows: %.0f ms (%d repeated)", (System.nanoTime() - t) / 1e6, r));
    }

    // ---------- J10 ----------
    static void j10() {
        Random rng = new Random(10);
        for (int t = 0; t < 100; t++) {
            List<String> order = new ArrayList<>(), stock = new ArrayList<>();
            for (int i = 0, n = rng.nextInt(30); i < n; i++) order.add("I" + rng.nextInt(10));
            for (int i = 0, n = rng.nextInt(10); i < n; i++) stock.add("I" + rng.nextInt(10));
            out(outcome(() -> Supplies.notStocked(order, stock)));
        }
    }

    // ---------- JW1 (write mode; checked against an independent reference) ----------
    static void jw1() throws Exception {
        Class<?> type;
        try {
            type = Class.forName("com.example.clinic.CoverageReport");
        } catch (ClassNotFoundException e) {
            out("no CoverageReport class");
            return;
        }
        Constructor<?> ctor = type.getConstructor(Availability.class);
        Method m = type.getMethod("uncoveredDays", List.class, LocalDate.class, LocalDate.class, int.class);
        Random rng = new Random(14);
        LocalDate base = LocalDate.of(2026, 1, 1);
        int mismatches = 0, trips = 0, cases = 0;
        for (int t = 0; t < 40; t++) {
            int doctors = 1 + rng.nextInt(6);
            Map<Long, Set<LocalDate>> rostered = new HashMap<>(), onLeave = new HashMap<>();
            for (long d = 1; d <= doctors; d++) {
                Set<LocalDate> r = new HashSet<>(), l = new HashSet<>();
                for (int i = 0; i < 60; i++) {
                    if (rng.nextInt(3) > 0) r.add(base.plusDays(i));
                    if (rng.nextInt(4) == 0) l.add(base.plusDays(i));
                }
                rostered.put(d, r);
                onLeave.put(d, l);
            }
            AtomicInteger calls = new AtomicInteger();
            ScheduleClient sc = (doc, from, to) -> { calls.incrementAndGet(); return within(rostered.getOrDefault(doc, Set.of()), from, to); };
            LeaveClient lc = (doc, from, to) -> { calls.incrementAndGet(); return within(onLeave.getOrDefault(doc, Set.of()), from, to); };
            List<Long> ids = new ArrayList<>();
            for (long d = 1; d <= doctors; d++) ids.add(d);
            LocalDate from = base.plusDays(rng.nextInt(20)), to = from.plusDays(rng.nextInt(40));
            int min = rng.nextInt(doctors + 2);
            List<LocalDate> expected = new ArrayList<>();
            for (LocalDate day = from; !day.isAfter(to); day = day.plusDays(1)) {
                int available = 0;
                for (long d : ids) if (rostered.get(d).contains(day) && !onLeave.get(d).contains(day)) available++;
                if (available < min) expected.add(day);
            }
            Object got;
            try {
                got = m.invoke(ctor.newInstance(new Availability(sc, lc)), ids, from, to, min);
            } catch (Exception e) {
                got = "raises " + e.getCause();
            }
            cases++;
            trips += calls.get();
            if (!expected.equals(got)) {
                mismatches++;
                if (mismatches <= 3) out("mismatch: doctors " + ids + " " + from + ".." + to + " min " + min + "\n  expected " + expected + "\n  got      " + got);
            }
        }
        out(mismatches + " mismatches in " + cases + " cases; " + trips + " round trips in all (about " + trips / cases + " per report)");
    }

    static Set<LocalDate> within(Set<LocalDate> days, LocalDate from, LocalDate to) {
        Set<LocalDate> r = new HashSet<>();
        for (LocalDate d : days) if (!d.isBefore(from) && !d.isAfter(to)) r.add(d);
        return r;
    }
}
