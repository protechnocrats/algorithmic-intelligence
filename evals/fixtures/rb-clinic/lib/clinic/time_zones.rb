# frozen_string_literal: true

module Clinic
  # Checks run when an administrator saves a clinic's settings.
  module TimeZones
    # Pairs of the clinic's opening-hour zones whose UTC offsets are equal, as [a, b] names in input order.
    def self.duplicate_offsets(zones)
      pairs = []
      zones.each_with_index do |a, i|
        zones.each_with_index do |b, j|
          pairs << [a[:name], b[:name]] if i < j && a[:utc_offset_minutes] == b[:utc_offset_minutes]
        end
      end
      pairs
    end
  end
end
