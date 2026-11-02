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
      prev = sorted.map { |r| sorted.bsearch_index { |q| q.finish > r.start } || sorted.size }
      dp = [0]
      sorted.each_with_index { |r, i| dp << [dp[i], r.value + dp[prev[i]]].max }
      dp.last
    end
  end
end
