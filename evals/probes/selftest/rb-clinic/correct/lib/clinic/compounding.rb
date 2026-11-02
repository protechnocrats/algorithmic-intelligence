# frozen_string_literal: true

module Clinic
  # Correct: for each first vial, scan the third while counting the middle values seen, O(n^2) expected.
  # Hash keys match with eql?, so a Float dose is turned into the Integer it equals (or matches nothing).
  module Compounding
    def self.three_vial_fills(vials_ug, dose_ug)
      if dose_ug.is_a?(Float)
        return 0 unless dose_ug.finite? && dose_ug == dose_ug.floor

        dose_ug = dose_ug.to_i
      end
      count = 0
      n = vials_ug.size
      (0...n).each do |i|
        middle = Hash.new(0)
        ((i + 1)...n).each do |k|
          count += middle[dose_ug - vials_ug[i] - vials_ug[k]]
          middle[vials_ug[k]] += 1
        end
      end
      count
    end
  end
end
