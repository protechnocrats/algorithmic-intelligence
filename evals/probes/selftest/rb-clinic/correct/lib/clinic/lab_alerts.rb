module Clinic
  module LabAlerts
    def self.repeat_tests(results, window_days)
      seen = Hash.new { |h, k| h[k] = [] }
      results.select do |r|
        dates = seen[[r.patient_id, r.test_code]]
        i = dates.bsearch_index { |d| d >= r.taken_on } || dates.size
        hit = (i < dates.size && dates[i] - r.taken_on <= window_days) || (i.positive? && r.taken_on - dates[i - 1] <= window_days)
        dates.insert(i, r.taken_on)
        hit
      end
    end
  end
end
