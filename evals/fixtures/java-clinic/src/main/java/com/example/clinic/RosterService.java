package com.example.clinic;

import java.util.ArrayList;
import java.util.List;

/** Builds the printed daily roster that wards receive each morning. */
public final class RosterService {
    private final PatientDirectory directory;

    public RosterService(PatientDirectory directory) {
        this.directory = directory;
    }

    /**
     * One line per appointment, in the order given.
     *
     * @throws PatientNotFoundException if an appointment refers to a patient with no record
     */
    public List<RosterLine> dailyRoster(List<Appointment> appointments) {
        List<RosterLine> lines = new ArrayList<>();
        for (Appointment appointment : appointments) {
            Patient patient = directory.fetch(appointment.patientId());
            lines.add(new RosterLine(appointment.id(), clock(appointment.start()), patient.displayName(), patient.ward()));
        }
        return lines;
    }

    private static String clock(int minutes) {
        return String.format("%02d:%02d", minutes / 60, minutes % 60);
    }
}
