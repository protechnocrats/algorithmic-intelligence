# frozen_string_literal: true

module Clinic
  # Weight-based dosing bands by age, used by the nightly dose check.
  module Pediatrics
    MAX_AGE_DAYS = 54_750

    # [first day, last day (inclusive), band, mg per kg], from the formulary.
    BANDS = [
      [0, 6, "neonate, first week", 2.0], [7, 27, "neonate", 2.5], [28, 89, "infant, 1-3 months", 3.0],
      [90, 181, "infant, 3-6 months", 3.5], [182, 366, "infant, 6-12 months", 4.0],
      [365, 729, "toddler, 1-2 years", 4.5], [730, 1094, "toddler, 2-3 years", 5.0],
      [1095, 1459, "child, 3 years", 5.0], [1460, 1824, "child, 4 years", 5.5], [1825, 2189, "child, 5 years", 5.5],
      [2190, 2554, "child, 6 years", 6.0], [2555, 2919, "child, 7 years", 6.0], [2920, 3284, "child, 8 years", 6.0],
      [3285, 3649, "child, 9 years", 6.5], [3650, 4014, "child, 10 years", 6.5], [4015, 4379, "child, 11 years", 6.5],
      [4380, 4744, "adolescent, 12 years", 7.0], [4745, 5109, "adolescent, 13 years", 7.0],
      [5110, 5474, "adolescent, 14 years", 7.0], [5475, 5839, "adolescent, 15 years", 7.5],
      [5840, 6204, "adolescent, 16 years", 7.5], [6205, 6569, "adolescent, 17 years", 7.5],
      [6570, 9124, "adult, 18-24", 8.0], [9125, 12_774, "adult, 25-34", 8.0], [12_775, 16_424, "adult, 35-44", 8.0],
      [16_425, 20_074, "adult, 45-54", 8.0], [20_075, 23_724, "adult, 55-64", 7.5], [23_725, 27_374, "older adult, 65-74", 7.0],
      [27_375, 31_024, "older adult, 75-84", 6.5], [31_025, MAX_AGE_DAYS, "older adult, 85 and over", 6.0]
    ].freeze

    # The dosing band for a patient's age in whole days.
    def self.band_for(age_days)
      raise ArgumentError, "age out of range: #{age_days.inspect}" unless age_days.is_a?(Integer) && age_days.between?(0, MAX_AGE_DAYS)

      i = BANDS.bsearch_index { |first, _, _, _| first > age_days } || BANDS.size
      first, last, band, mg = BANDS[i - 1]
      age_days <= last ? [band, mg] : nil
    end
  end
end
