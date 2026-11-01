# frozen_string_literal: true

module Clinic
  # Infusion-pump log analysis for the monthly safety report.
  module Dosing
    # The number of windows of consecutive log entries whose total is between low
    # and high (inclusive) and in which no entry is above cap. Entries are integer
    # milligrams in log order. The pump logs a negative entry when it reverses a
    # mis-logged dose.
    def self.count_windows(entries, low, high, cap)
      count = 0
      (0...entries.size).each do |i|
        (i...entries.size).each do |j|
          window = entries[i..j]
          count += 1 if window.max <= cap && window.sum.between?(low, high)
        end
      end
      count
    end
  end
end
