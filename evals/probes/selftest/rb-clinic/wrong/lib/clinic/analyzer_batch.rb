# frozen_string_literal: true

module Clinic
  # Wrong: plain 0/1 knapsack. It ignores the one-sample-per-patient rule.
  module AnalyzerBatch
    Sample = Struct.new(:sample_id, :patient_id, :reagent_ul, :urgency, keyword_init: true) do
      def initialize(**)
        super
        raise ArgumentError, "reagent use cannot be negative" if reagent_ul.negative?
      end
    end

    def self.best_urgency(pending, capacity_ul)
      return 0 if capacity_ul.negative?

      best = Array.new(capacity_ul + 1, 0)
      pending.each do |s|
        capacity_ul.downto(s.reagent_ul) do |c|
          v = best[c - s.reagent_ul] + s.urgency
          best[c] = v if v > best[c]
        end
      end
      best[capacity_ul]
    end
  end
end
