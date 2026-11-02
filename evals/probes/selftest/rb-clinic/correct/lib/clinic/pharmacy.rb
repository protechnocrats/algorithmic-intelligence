# frozen_string_literal: true

module Clinic
  # Pharmacy reconciliation.
  module Pharmacy
    # The prescription ids that have not been dispensed, in order, repeats kept.
    # Ids come from the hospital's own prescribing system.
    def self.undispensed(prescription_ids, dispensed_ids)
      dispensed = dispensed_ids.to_set
      prescription_ids.reject { |id| dispensed.include?(id) }
    end
  end
end
