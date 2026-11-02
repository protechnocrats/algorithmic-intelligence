# frozen_string_literal: true

module Clinic
  # Correct: knapsack with one choice per patient group, O(n * capacity), capacity iterated downward against the previous groups' table.
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
      pending.group_by(&:patient_id).each_value do |group|
        nxt = best.dup
        group.each do |s|
          capacity_ul.downto(s.reagent_ul) do |c|
            v = best[c - s.reagent_ul] + s.urgency
            nxt[c] = v if v > nxt[c]
          end
        end
        best = nxt
      end
      best[capacity_ul]
    end
  end
end
