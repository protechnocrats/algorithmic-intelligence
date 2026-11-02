# frozen_string_literal: true

module Clinic
  # The pharmacy's compounding bench.
  module Compounding
    # The number of ways an order can be filled from exactly three different
    # vials on the shelf: unordered triples of distinct vials whose contents add
    # up to the ordered dose. Contents are integer micrograms. The dose comes
    # from the order-entry system's JSON, so it can arrive as 600 or as 600.0.
    def self.three_vial_fills(vials_ug, dose_ug)
      count = 0
      n = vials_ug.size
      (0...n).each do |i|
        ((i + 1)...n).each do |j|
          ((j + 1)...n).each do |k|
            count += 1 if vials_ug[i] + vials_ug[j] + vials_ug[k] == dose_ug
          end
        end
      end
      count
    end
  end
end
