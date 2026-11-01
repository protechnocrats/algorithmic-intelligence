package com.example.clinic;

import static com.example.clinic.testing.Assert.assertEquals;
import static com.example.clinic.testing.Assert.assertThrows;
import static com.example.clinic.testing.Assert.assertTrue;

import com.example.clinic.testing.Test;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public class ClinicTest {

    static final class InMemoryDirectory implements PatientDirectory {
        final Map<Long, Patient> records = new HashMap<>();
        int roundTrips;

        InMemoryDirectory add(long id, String name, String ward) {
            records.put(id, new Patient(id, name, ward));
            return this;
        }

        @Override public Patient fetch(long patientId) {
            roundTrips++;
            Patient p = records.get(patientId);
            if (p == null) throw new PatientNotFoundException(patientId);
            return p;
        }

        @Override public Map<Long, Patient> fetchAll(Collection<Long> ids) {
            if (ids.size() > 500) throw new IllegalArgumentException("at most 500 ids");
            roundTrips++;
            Map<Long, Patient> found = new HashMap<>();
            for (long id : ids) if (records.containsKey(id)) found.put(id, records.get(id));
            return found;
        }
    }

    @Test public void rosterListsAppointmentsInOrder() {
        InMemoryDirectory directory = new InMemoryDirectory().add(1, "Ada Byrne", "W3").add(2, "Tom Ochoa", "W1");
        List<RosterLine> lines = new RosterService(directory).dailyRoster(List.of(
                new Appointment(10, 2, 9 * 60, 9 * 60 + 20),
                new Appointment(11, 1, 9 * 60 + 5, 9 * 60 + 30),
                new Appointment(12, 2, 14 * 60, 14 * 60 + 15)));
        assertEquals(List.of(
                new RosterLine(10, "09:00", "Tom Ochoa", "W1"),
                new RosterLine(11, "09:05", "Ada Byrne", "W3"),
                new RosterLine(12, "14:00", "Tom Ochoa", "W1")), lines);
    }

    @Test public void formatterLabelsKnownCodes() {
        CodeFormatter f = new CodeFormatter(List.of(new Term("LAB 2345-7", "Glucose"), new Term("LAB 718-7", "Hemoglobin")));
        assertEquals("LAB 2345-7 Glucose", f.label(" lab:2345 7 "));
        assertEquals("LAB 718-7 Hemoglobin", f.label("Lab-718-7"));
        assertEquals("UNKNOWN xyz", f.label(" xyz "));
    }

    @Test public void formatterUsesReloadedTerminology() {
        CodeFormatter f = new CodeFormatter(List.of(new Term("LAB 2345-7", "Glucose")));
        f.reload(List.of(new Term("LAB 2345-7", "Glucose, serum")));
        assertEquals("LAB 2345-7 Glucose, serum", f.label("LAB 2345-7"));
    }

    static final class RecordingGateway implements SmsGateway {
        final List<Long> delivered = new ArrayList<>();
        final Set<String> invalidNumbers = new HashSet<>();

        @Override public void send(Reminder r) {
            if (invalidNumbers.contains(r.phoneNumber())) throw new GatewayException("invalid number");
            delivered.add(r.id());
        }

        @Override public void sendBatch(List<Reminder> rs) {
            for (Reminder r : rs) if (invalidNumbers.contains(r.phoneNumber())) throw new GatewayException("invalid number");
            for (Reminder r : rs) delivered.add(r.id());
        }
    }

    @Test public void remindersReportRejections() {
        RecordingGateway gateway = new RecordingGateway();
        gateway.invalidNumbers.add("+15550000");
        SendReport report = new ReminderSender(gateway, 0).sendAll(List.of(
                new Reminder(1, "+15551234", "See you at 9:00"),
                new Reminder(2, "+15550000", "See you at 9:30"),
                new Reminder(3, "+15559876", "See you at 10:00")));
        assertEquals(new SendReport(2, List.of(2L)), report);
        assertEquals(List.of(1L, 3L), gateway.delivered);
    }

    @Test public void chartViewerShowsLatestEntries() {
        Map<Long, Chart> charts = Map.of(
                5L, new Chart(5, 1, List.of("admitted", "stable")),
                6L, new Chart(6, 2, List.of()));
        List<String> latest = ChartViewer.latestEntries(new ChartRepository(charts::get), List.of(5L, 6L, 5L));
        assertEquals(List.of("stable", "", "stable"), latest);
    }

    @Test public void roomsForOverlappingAppointments() {
        assertEquals(0, RoomPlanner.roomsNeeded(List.of()));
        assertEquals(2, RoomPlanner.roomsNeeded(List.of(
                new Appointment(1, 1, 540, 600), new Appointment(2, 2, 570, 630), new Appointment(3, 3, 600, 660))));
        assertThrows(IllegalArgumentException.class,
                () -> RoomPlanner.roomsNeeded(List.of(new Appointment(1, 1, 600, 600))));
    }

    @Test public void weeklyRoomsCountSlotsAcrossTheWeekBoundary() {
        int sunday2300 = 6 * 1440 + 23 * 60;
        assertEquals(2, RoomPlanner.weeklyRoomsNeeded(List.of(
                new WeeklySlot(1, sunday2300, 120), new WeeklySlot(2, 30, 60), new WeeklySlot(3, 600, 60))));
        assertEquals(1, RoomPlanner.weeklyRoomsNeeded(List.of(new WeeklySlot(1, sunday2300, 60), new WeeklySlot(2, 0, 60))));
    }

    @Test public void minutesUntilOpen() {
        SessionCalendar outpatients = SessionCalendar.outpatients();
        assertEquals(0, outpatients.minutesUntilOpen(8 * 60));
        assertEquals(60, outpatients.minutesUntilOpen(7 * 60));
        assertEquals(1440 - 21 * 60 + 8 * 60, outpatients.minutesUntilOpen(21 * 60));
        assertEquals(-1, new SessionCalendar(List.of()).minutesUntilOpen(100));
        assertThrows(IllegalArgumentException.class, () -> outpatients.minutesUntilOpen(SessionCalendar.MINUTES_PER_WEEK));
    }

    @Test public void ledgerRangeTotals() {
        double[] totals = Ledger.rangeTotals(new double[] {10, 20, 30, 40}, List.of(new Range(0, 2), new Range(1, 4), new Range(2, 2)));
        assertEquals(30.0, totals[0]);
        assertEquals(90.0, totals[1]);
        assertEquals(0.0, totals[2]);
        assertThrows(IllegalArgumentException.class, () -> Ledger.rangeTotals(new double[3], List.of(new Range(2, 4))));
    }

    @Test public void repeatedVisitsInFirstAppearanceOrder() {
        VisitKey a = new VisitKey(1, 10), b = new VisitKey(2, 10), c = new VisitKey(1, 11);
        assertEquals(List.of(b, a), PartnerImport.repeatedVisits(List.of(b, a, c, a, b, b)));
        assertEquals(List.of(), PartnerImport.repeatedVisits(List.of(a, b, c)));
    }

    @Test public void notStockedKeepsOrderAndRepeats() {
        assertEquals(List.of("GAUZE-5", "TAPE-2", "GAUZE-5"),
                Supplies.notStocked(List.of("GAUZE-5", "SAL-1", "TAPE-2", "GAUZE-5"), List.of("SAL-1", "GLOVE-M")));
    }

    @Test public void availabilityExcludesLeave() {
        LocalDate monday = LocalDate.of(2026, 11, 2);
        ScheduleClient schedules = (doctor, from, to) -> Set.of(monday, monday.plusDays(1));
        LeaveClient leave = (doctor, from, to) -> Set.of(monday.plusDays(1));
        Availability availability = new Availability(schedules, leave);
        assertTrue(availability.isAvailable(7, monday), "rostered and not on leave");
        assertTrue(!availability.isAvailable(7, monday.plusDays(1)), "on leave");
        assertEquals(Set.of(monday, monday.plusDays(1)), availability.rosteredDays(7, monday, monday.plusDays(6)));
    }
}
