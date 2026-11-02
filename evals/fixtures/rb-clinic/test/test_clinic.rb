# frozen_string_literal: true

require "minitest/autorun"
require "date"
require "fileutils"
require "tmpdir"
require "clinic"

class FakePrices
  attr_reader :round_trips

  def initialize(history)
    @history = history # code => [[date, cents], ...] oldest first
    @round_trips = 0
  end

  def price_on(code, date)
    @round_trips += 1
    changes = @history.fetch(code) { raise Clinic::UnknownCode, code }
    change = changes.reverse.find { |from, _| from <= date }
    raise Clinic::NoPriceOnDate, "#{code} #{date}" unless change

    change[1]
  end

  def current_prices(codes)
    @round_trips += 1
    codes.select { |c| @history.key?(c) }.to_h { |c| [c, @history[c].last[1]] }
  end

  def price_history(code)
    @round_trips += 1
    @history.fetch(code) { raise Clinic::UnknownCode, code }
  end
end

class ClinicTest < Minitest::Test
  def test_statement_lines_use_the_price_on_the_service_date
    prices = FakePrices.new("X1" => [[Date.new(2026, 1, 1), 1000], [Date.new(2026, 6, 1), 1200]])
    lines = Clinic::Billing.new(prices).statement_lines([
      Clinic::VisitLine.new(code: "X1", service_date: Date.new(2026, 3, 1), quantity: 2),
      Clinic::VisitLine.new(code: "X1", service_date: Date.new(2026, 7, 1), quantity: 1)
    ])
    assert_equal [2000, 1200], lines.map(&:total_cents)
  end

  def test_display_names_come_from_the_label_file
    labels = Clinic::Labels.new(File.expand_path("../config/labels.yml", __dir__))
    assert_equal "Procedure 7", labels.display_name("BC0007")
    assert_equal "Unlisted (ZZ1)", labels.display_name("ZZ1")
  end

  def test_code_summary_marks_discontinued_codes
    labels = Clinic::Labels.new(File.expand_path("../config/labels.yml", __dir__))
    rows = Clinic::CodeSummary.rows([["BC0001", 3, false], ["BC0002", 1, true]], labels)
    assert_equal [["Procedure 1", 3], ["Procedure 2 (discontinued)", 1]], rows
  end

  def test_exports_append_to_each_clinics_file
    Dir.mktmpdir do |dir|
      File.write(File.join(dir, "7.csv"), "7,1,OLD,5\n")
      rows = [Clinic::ExportRow.new(clinic_id: 7, patient_id: 2, code: "A", amount_cents: 10),
              Clinic::ExportRow.new(clinic_id: 8, patient_id: 3, code: "B", amount_cents: 20),
              Clinic::ExportRow.new(clinic_id: 7, patient_id: 4, code: "C", amount_cents: 30)]
      Clinic::Exports.append_by_clinic(rows, dir)
      assert_equal "7,1,OLD,5\n7,2,A,10\n7,4,C,30\n", File.read(File.join(dir, "7.csv"))
      assert_equal "8,3,B,20\n", File.read(File.join(dir, "8.csv"))
    end
  end

  def test_duplicate_offsets
    zones = [{ name: "Lisbon", utc_offset_minutes: 0 }, { name: "Accra", utc_offset_minutes: 0 },
             { name: "Lagos", utc_offset_minutes: 60 }]
    assert_equal [%w[Lisbon Accra]], Clinic::TimeZones.duplicate_offsets(zones)
  end

  def test_count_windows
    assert_equal 0, Clinic::Dosing.count_windows([], 0, 10, 5)
    assert_equal 2, Clinic::Dosing.count_windows([2, 3, 9, 1], 3, 5, 5)
  end

  def test_best_total_respects_one_booking_per_patient
    r = Clinic::ProcedureRoom::Request
    requests = [r.new(id: 1, patient_id: 1, start: 540, finish: 600, value: 5),
                r.new(id: 2, patient_id: 1, start: 600, finish: 660, value: 4),
                r.new(id: 3, patient_id: 2, start: 570, finish: 630, value: 6)]
    assert_equal 6, Clinic::ProcedureRoom.best_total(requests)
    assert_equal 0, Clinic::ProcedureRoom.best_total([])
  end

  def test_band_for
    assert_equal ["neonate", 2.5], Clinic::Pediatrics.band_for(10)
    assert_equal ["adult, 25-34", 8.0], Clinic::Pediatrics.band_for(10_000)
    assert_raises(ArgumentError) { Clinic::Pediatrics.band_for(-1) }
  end

  def test_queue_order_puts_higher_acuity_first
    p = Clinic::Triage::Patient
    waiting = [p.new(id: 1, acuity: 2), p.new(id: 2, acuity: 5), p.new(id: 3, acuity: 3)]
    assert_equal [2, 3, 1], Clinic::Triage.queue_order(waiting).map(&:id)
  end

  def test_undispensed_keeps_order_and_repeats
    assert_equal [4, 9, 4], Clinic::Pharmacy.undispensed([4, 5, 9, 4], [5, 7])
  end

  def test_signature_matches_only_identical_bytes
    sig = "\x01\x02\x03\x04".b
    assert Clinic::LabCallbacks.signature_matches?(sig, "\x01\x02\x03\x04".b)
    refute Clinic::LabCallbacks.signature_matches?(sig, "\x01\x02\x03\x05".b)
    refute Clinic::LabCallbacks.signature_matches?(sig, "\x01\x02\x03".b)
    refute Clinic::LabCallbacks.signature_matches?(sig, nil)
  end

  def test_analyzer_batch_one_sample_per_patient
    s = Clinic::AnalyzerBatch::Sample
    pending = [s.new(sample_id: 1, patient_id: 100, reagent_ul: 40, urgency: 9), s.new(sample_id: 2, patient_id: 100, reagent_ul: 10, urgency: 5),
               s.new(sample_id: 3, patient_id: 200, reagent_ul: 50, urgency: 7), s.new(sample_id: 4, patient_id: 300, reagent_ul: 30, urgency: 4)]
    assert_equal 16, Clinic::AnalyzerBatch.best_urgency(pending, 90)
    assert_equal 9, Clinic::AnalyzerBatch.best_urgency(pending, 50)
    assert_equal 0, Clinic::AnalyzerBatch.best_urgency(pending, 5)
  end

  def test_three_vial_fills_counts_distinct_vials
    assert_equal 2, Clinic::Compounding.three_vial_fills([100, 200, 300, 200, 400], 600)
    assert_equal 0, Clinic::Compounding.three_vial_fills([100, 200], 300)
  end
end
