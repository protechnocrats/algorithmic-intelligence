package com.example.clinic;

import java.util.Collection;
import java.util.Map;

/**
 * Client for the hospital records service. Every call is one HTTPS round trip
 * (about 2 ms at p50 and 15 ms at p99 from the application servers).
 */
public interface PatientDirectory {
    /**
     * The record for one patient.
     *
     * @throws PatientNotFoundException if the service has no record for the id
     */
    Patient fetch(long patientId);

    /**
     * Records for up to 500 patients in one round trip. Ids may repeat. Ids with
     * no record are left out of the result.
     *
     * @throws IllegalArgumentException if more than 500 ids are given
     */
    Map<Long, Patient> fetchAll(Collection<Long> patientIds);
}
