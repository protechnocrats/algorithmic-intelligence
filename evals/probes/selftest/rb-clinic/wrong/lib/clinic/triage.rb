# frozen_string_literal: true

module Clinic
  # The emergency department waiting board.
  module Triage
    Patient = Struct.new(:id, :acuity, :arrived_at, keyword_init: true)

    # The waiting list in the order patients should be seen, highest acuity
    # first. waiting is in arrival order.
    def self.queue_order(waiting)
      waiting.sort_by { |p| -p.acuity }
    end
  end
end
