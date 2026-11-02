# frozen_string_literal: true

module Clinic
  # Infusion-pump log analysis for the monthly safety report.
  module Dosing
    # The number of windows of consecutive log entries whose total is between low
    # and high (inclusive) and in which no entry is above cap. Entries are integer
    # milligrams in log order. The pump logs a negative entry when it reverses a
    # mis-logged dose.
    def self.count_windows(entries, low, high, cap)
      return 0 if low > high

      entries.slice_when { |a, b| (a > cap) != (b > cap) }.reject { |seg| seg.first > cap }.sum { |seg| count_segment(seg, low, high) }
    end

    def self.count_segment(seg, low, high)
      prefix = [0]
      seg.each { |x| prefix << prefix.last + x }
      values = prefix.uniq.sort
      tree = Array.new(values.size + 1, 0)
      add = ->(v) { i = values.bsearch_index { |x| x >= v } + 1; (tree[i] += 1; i += i & -i) while i <= values.size }
      upto = ->(v) { i = values.bsearch_index { |x| x > v } || values.size; s = 0; (s += tree[i]; i -= i & -i) while i.positive?; s }
      count = 0
      prefix.each do |p|
        count += upto.(p - low) - upto.(p - high - 1)
        add.(p)
      end
      count
    end
  end
end
