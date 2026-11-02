# frozen_string_literal: true

module Clinic
  # Wrong: sorts the caller's array in place, and looks up a Float dose's complements in an Integer-keyed hash (eql? fails).
  module Compounding
    def self.three_vial_fills(vials_ug, dose_ug)
      vials_ug.sort!
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
