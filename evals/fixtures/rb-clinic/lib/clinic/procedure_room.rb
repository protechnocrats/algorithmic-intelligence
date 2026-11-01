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
      best = 0
      (1..requests.size).each do |k|
        requests.combination(k) do |chosen|
          next unless chosen.map(&:patient_id).uniq.size == chosen.size

          sorted = chosen.sort_by(&:start)
          next unless sorted.each_cons(2).all? { |a, b| a.finish <= b.start }

          total = chosen.sum(&:value)
          best = total if total > best
        end
      end
      best
    end
  end
end
