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
      rows.group_by(&:clinic_id).each do |clinic_id, clinic_rows|
        File.open(File.join(dir, "#{clinic_id}.csv"), "a") { |f| clinic_rows.each { |row| f.puts(row.to_csv_line) } }
      end
      nil
    end
  end
end
