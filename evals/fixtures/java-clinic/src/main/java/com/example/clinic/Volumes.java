package com.example.clinic;

/** Production volumes, from the capacity-planning sheet (reviewed each quarter). */
public final class Volumes {
    private Volumes() {}

    /** Appointments on the whole-hospital daily roster. */
    public static final int APPOINTMENTS_PER_DAILY_ROSTER = 2_000;
    /** Lab results ingested per day, across 16 ingestion threads. */
    public static final int LAB_RESULTS_PER_DAY = 5_000_000;
    /** Distinct raw code strings seen per day. Most are free text from partner labs and few repeat on later days. */
    public static final int DISTINCT_RAW_LAB_CODES_PER_DAY = 400_000;
    /** Entries in the lab terminology, reloaded on the first of each month. */
    public static final int TERMINOLOGY_ENTRIES = 90_000;
    /** The ingestion service is restarted only for deployments, typically every few weeks. */
    public static final int INGESTION_UPTIME_DAYS_TYPICAL = 21;
    /** Appointment reminders sent per night. */
    public static final int REMINDERS_PER_NIGHT = 30_000;
    /** Share of reminders the SMS provider rejects (invalid or disconnected numbers). */
    public static final double REMINDER_REJECTION_RATE = 0.01;
    /** Charts opened per chart-viewer request, and distinct charts among them. */
    public static final int CHARTS_PER_VIEWER_REQUEST_MAX = 12;
    public static final int DISTINCT_CHARTS_PER_VIEWER_REQUEST_MAX = 3;
    /** Appointments in one department's daily room plan. */
    public static final int APPOINTMENTS_PER_ROOM_PLAN = 400;
    /** Recurring weekly slots per clinic (the weekly room plan). */
    public static final int WEEKLY_SLOTS_PER_CLINIC = 60;
    /** minutesUntilOpen calls per night from the referral routing job. */
    public static final int ROUTING_LOOKUPS_PER_NIGHT = 40_000_000;
    /** Ledger entries per account in a statement run, and ranges requested per run. */
    public static final int LEDGER_ENTRIES_PER_ACCOUNT = 1_000_000;
    public static final int RANGES_PER_STATEMENT_RUN = 20_000;
    /** Statement ranges start on a statement-period boundary: at most this many distinct starts per run. */
    public static final int STATEMENT_PERIODS_PER_RUN = 24;
    /** Rows in one partner-hospital upload (the import endpoint's limit). */
    public static final int PARTNER_UPLOAD_ROWS_MAX = 200_000;
    /** Items on one supply order, and items in a ward's stock list. */
    public static final int ITEMS_PER_SUPPLY_ORDER = 20_000;
    public static final int ITEMS_IN_WARD_STOCK = 30_000;
    /** Coverage reports: doctors per report and days per report. */
    public static final int DOCTORS_PER_COVERAGE_REPORT = 50;
    public static final int DAYS_PER_COVERAGE_REPORT_MAX = 366;
}
