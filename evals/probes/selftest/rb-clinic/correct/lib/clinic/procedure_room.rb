# frozen_string_literal: true

module Clinic
  # Booking for the day-procedure room.
  module ProcedureRoom
    # A requested booking from start to finish (minutes after midnight; finish
    # is exclusive), worth value to the department.
    Request = Struct.new(:id, :patient_id, :start, :finish, :value, keyword_init: true)

    # The largest total value of requests that can be booked for the day. Booked
    # requests may not overlap (back to back is fine), and each patient gets at
    # most one booking: many patients send several alternative times.
    def self.best_total(requests)
      sorted = requests.sort_by(&:finish)
      counts = sorted.map(&:patient_id).tally
      bit = {}
      counts.each_key { |p| bit[p] = 1 << bit.size if counts[p] > 1 }
      full = (1 << bit.size) - 1
      prev = sorted.map { |r| sorted.bsearch_index { |q| q.finish > r.start } || sorted.size }
      dp = [Array.new(full + 1, 0)]
      sorted.each_with_index do |r, i|
        b = bit.fetch(r.patient_id, 0)
        row = dp[i].dup
        (0..full).each do |mask|
          next unless b.zero? || mask & b != 0

          take = r.value + dp[prev[i]][mask & ~b]
          row[mask] = take if take > row[mask]
        end
        dp << row
      end
      dp.last[full]
    end
  end
end
