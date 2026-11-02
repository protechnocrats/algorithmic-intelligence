# frozen_string_literal: true

module Clinic
  # Typical production volumes, from the operations runbook.
  VOLUMES = {
    statements_per_night: 3_000,
    lines_per_statement_max: 2_000, # long inpatient stays
    distinct_codes_per_statement: 40,
    rows_per_code_summary: 300_000,
    label_file_entries: 2_000,
    export_rows: 2_000_000,
    clinics_per_export: 5_000,
    export_worker_open_files_limit: 1_024, # container default
    time_zones_per_clinic_max: 5,
    pump_log_entries_per_month: 50_000,
    procedure_requests_per_room_day: 60,
    patients_with_alternative_times_per_day_max: 12,
    dose_checks_per_night: 40_000_000, # regional dose-check service, 30 hospitals
    waiting_list_size_max: 5_000,
    waiting_board_refreshes_per_minute: 240, # 40 boards, every 10 seconds
    prescriptions_per_batch: 50_000,
    dispensed_records_per_batch: 50_000,
    lab_results_per_night: 500_000,
    lab_results_arrive_late_by_days_max: 10,
    repeat_test_window_days_max: 30,
    lab_callbacks_per_day: 1_200_000,
    analyzer_runs_per_day: 48,
    samples_pending_per_run: 90,
    analyzer_reagent_per_run_ul: 2_500,
    vials_on_compounding_shelf: 6_000,
    compounding_orders_per_day: 300
  }.freeze
end
