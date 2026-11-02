module Clinic
  module Dosing
    # Two pointers: windows with sum <= high minus windows with sum <= low - 1, per segment split at entries above cap.
    def self.count_windows(entries, low, high, cap)
      return 0 if low > high

      at_most(entries, high, cap) - at_most(entries, low - 1, cap)
    end

    def self.at_most(entries, limit, cap)
      count = 0
      left = 0
      sum = 0
      entries.each_with_index do |x, right|
        if x > cap
          left = right + 1
          sum = 0
          next
        end
        sum += x
        while left <= right && sum > limit
          sum -= entries[left]
          left += 1
        end
        count += right - left + 1
      end
      count
    end
  end
end
