# frozen_string_literal: true

module Clinic
  # The emergency department waiting board.
  module Triage
    Patient = Struct.new(:id, :acuity, :arrived_at, keyword_init: true)

    # The waiting list in the order patients should be seen, highest acuity
    # first. waiting is in arrival order.
    def self.queue_order(waiting)
      ordered = []
      waiting.each do |patient|
        i = ordered.size
        i -= 1 while i.positive? && ordered[i - 1].acuity < patient.acuity
        ordered.insert(i, patient)
      end
      ordered
    end
  end
end
