# frozen_string_literal: true

module Clinic
  ExportRow = Struct.new(:clinic_id, :patient_id, :code, :amount_cents, keyword_init: true) do
    def to_csv_line
      [clinic_id, patient_id, code, amount_cents].join(",")
    end
  end

  # The nightly export for clinic billing systems.
  module Exports
    # Appends each row to its clinic's file, dir/<clinic_id>.csv, keeping the
    # rows' order within each file. Files from earlier runs are kept and appended to.
    # dir is the billing share, an NFS mount.
    def self.append_by_clinic(rows, dir)
      files = Hash.new { |h, id| h[id] = File.open(File.join(dir, "#{id}.csv"), "a") }
      rows.each { |row| files[row.clinic_id].puts(row.to_csv_line) }
    ensure
      files&.each_value(&:close)
      nil
    end
  end
end
