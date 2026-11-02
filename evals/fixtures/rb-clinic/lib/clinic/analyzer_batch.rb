# frozen_string_literal: true

require "set"

module Clinic
  # Plans the next run of the chemistry analyzer.
  module AnalyzerBatch
    # A sample waiting for the analyzer. Reagent use is in microliters; urgency is
    # the triage score from the requesting ward.
    Sample = Struct.new(:sample_id, :patient_id, :reagent_ul, :urgency, keyword_init: true) do
      def initialize(**)
        super
        raise ArgumentError, "reagent use cannot be negative" if reagent_ul.negative?
      end
    end

    # The highest total urgency of samples that fit in one run's reagent capacity.
    # At most one sample per patient goes into a run: the analyzer's carousel
    # holds one tube per patient barcode.
    def self.best_urgency(pending, capacity_ul)
      best(pending, 0, capacity_ul, Set.new)
    end

    def self.best(pending, i, remaining, patients_in_run)
      return 0 if i == pending.size

      skip = best(pending, i + 1, remaining, patients_in_run)
      s = pending[i]
      return skip if s.reagent_ul > remaining || patients_in_run.include?(s.patient_id)

      patients_in_run.add(s.patient_id)
      take = s.urgency + best(pending, i + 1, remaining - s.reagent_ul, patients_in_run)
      patients_in_run.delete(s.patient_id)
      [skip, take].max
    end
    private_class_method :best
  end
end
