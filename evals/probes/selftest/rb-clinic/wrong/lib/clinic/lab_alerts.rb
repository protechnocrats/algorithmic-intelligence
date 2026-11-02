module Clinic
  module LabAlerts
    def self.repeat_tests(results, window_days)
      last = {}
      results.select do |r|
        key = [r.patient_id, r.test_code]
        hit = last.key?(key) && (r.taken_on - last[key]).abs <= window_days
        last[key] = r.taken_on
        hit
      end
    end
  end
end
