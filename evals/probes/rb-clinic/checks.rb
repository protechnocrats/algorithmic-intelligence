# Grading checks for rb-clinic. Run by evals/probes/rb-clinic.py inside the
# directory being graded: ruby -Ilib checks.rb <check>. Prints one result per line.
require "clinic"
require "date"
require "digest"
require "fileutils"
require "tmpdir"
require "yaml"

def outcome
  "ok #{yield.inspect}"
rescue StandardError => e
  "raises #{e.class}"
end

def clock
  s = Process.clock_gettime(Process::CLOCK_MONOTONIC)
  yield
  Process.clock_gettime(Process::CLOCK_MONOTONIC) - s
end

class Prices
  attr_reader :trips

  def initialize(history)
    @history = history
    @trips = 0
  end

  def price_on(code, date)
    @trips += 1
    changes = @history.fetch(code) { raise Clinic::UnknownCode, code }
    change = changes.reverse.find { |from, _| from <= date }
    raise Clinic::NoPriceOnDate, code unless change

    change[1]
  end

  def current_prices(codes)
    raise ArgumentError if codes.size > 200

    @trips += 1
    codes.select { |c| @history.key?(c) }.to_h { |c| [c, @history[c].last[1]] }
  end

  def price_history(code)
    @trips += 1
    @history.fetch(code) { raise Clinic::UnknownCode, code }.map(&:dup)
  end
end

def price_book(rng)
  (1..40).to_h do |c|
    d = Date.new(2024, 1, 1) - rng.rand(30)
    ["C#{c}", Array.new(1 + rng.rand(5)) { |i| [d + i * 120 + (i.zero? ? 0 : rng.rand(60)), 100 * (1 + rng.rand(50))] }]
  end
end

def visit_lines(rng, n, codes)
  Array.new(n) do
    Clinic::VisitLine.new(code: codes.sample(random: rng), service_date: Date.new(2024, 3, 1) + rng.rand(600), quantity: 1 + rng.rand(3))
  end
end

CHECKS = {
  "RB1" => lambda {
    rng = Random.new(1)
    book = price_book(rng)
    lines = visit_lines(rng, 1500, book.keys)
    puts outcome { Clinic::Billing.new(Prices.new(book)).statement_lines(lines).map(&:to_h) }
    puts outcome { Clinic::Billing.new(Prices.new(book)).statement_lines([]) }
    early = Clinic::VisitLine.new(code: "C1", service_date: Date.new(2000, 1, 1), quantity: 1)
    unknown = Clinic::VisitLine.new(code: "NOPE", service_date: Date.new(2025, 1, 1), quantity: 1)
    puts outcome { Clinic::Billing.new(Prices.new(book)).statement_lines(lines.first(5) + [early] + lines.first(3) + [unknown]) }
    puts outcome { Clinic::Billing.new(Prices.new(book)).statement_lines(lines.first(5) + [unknown] + [early]) }
    puts outcome { Clinic::Billing.new(Prices.new(book)).statement_lines([unknown]) }
  },
  "RB1-trips" => lambda {
    rng = Random.new(2)
    book = price_book(rng)
    prices = Prices.new(book)
    Clinic::Billing.new(prices).statement_lines(visit_lines(rng, 2000, book.keys))
    puts "#{prices.trips} round trips for 2,000 lines"
  },
  "RB2" => lambda {
    Dir.mktmpdir do |dir|
      path = File.join(dir, "labels.yml")
      File.write(path, { "A" => "Alpha", "B" => "Beta" }.to_yaml)
      labels = Clinic::Labels.new(path)
      puts outcome { [labels.display_name("A"), labels.display_name("Z")] }
      File.write(path, { "A" => "Alpha, revised", "Z" => "Zeta" }.to_yaml)
      File.utime(Time.now + 5, Time.now + 5, path)
      puts outcome { [labels.display_name("A"), labels.display_name("Z"), labels.display_name("B")] }
      File.write(path, { "A" => "Alpha, third" }.to_yaml) # same second, same size class
      puts outcome { labels.display_name("A") }
      name = labels.display_name("A")
      name << " (discontinued)" unless name.frozen?
      puts outcome { labels.display_name("A") }
      puts outcome { Clinic::CodeSummary.rows([["A", 1, true], ["A", 2, false], ["Q", 1, true], ["Q", 1, false]], labels) }
      File.delete(path)
      puts outcome { labels.display_name("A") }
    end
  },
  "RB2-time" => lambda {
    labels = Clinic::Labels.new(File.expand_path("config/labels.yml"))
    rows = Array.new(3000) { |i| ["BC#{format('%04d', i % 2000)}", i, i.even?] }
    puts format("3,000 summary rows: %.2f s", clock { Clinic::CodeSummary.rows(rows, labels) })
  },
  "RB3" => lambda {
    Process.setrlimit(:NOFILE, 256)
    Dir.mktmpdir do |dir|
      File.write(File.join(dir, "5.csv"), "earlier run\n")
      rng = Random.new(3)
      rows = Array.new(9000) { |i| Clinic::ExportRow.new(clinic_id: rng.rand(3000), patient_id: i, code: "X#{i % 7}", amount_cents: i) }
      rows << Clinic::ExportRow.new(clinic_id: 5, patient_id: -1, code: "L", amount_cents: 0)
      result = outcome { Clinic::Exports.append_by_clinic(rows, dir) }
      files = Dir.children(dir).sort.map { |f| "#{f}:#{Digest::SHA256.hexdigest(File.read(File.join(dir, f)))[0, 12]}" }
      puts result, files.size, Digest::SHA256.hexdigest(files.join(" "))
    end
  },
  "RB4" => lambda {
    rng = Random.new(4)
    50.times do
      zones = Array.new(rng.rand(6)) { |i| { name: "Z#{i}", utc_offset_minutes: [0, 60, -300, 330].sample(random: rng) } }
      puts outcome { Clinic::TimeZones.duplicate_offsets(zones) }
    end
  },
  "RB5" => lambda {
    rng = Random.new(5)
    600.times do
      e = Array.new(rng.rand(14)) { rng.rand(-6..9) }
      lo = rng.rand(-5..8)
      puts outcome { Clinic::Dosing.count_windows(e, lo, lo + rng.rand(-2..8), rng.rand(-2..9)) }
    end
  },
  "RB5-time" => lambda {
    rng = Random.new(6)
    e = Array.new(50_000) { rng.rand(10) < 1 ? -rng.rand(1..40) : rng.rand(0..60) }
    puts format("50,000 entries: %.2f s", clock { Clinic::Dosing.count_windows(e, 200, 400, 55) })
  },
  "RB6" => lambda {
    rng = Random.new(7)
    r = Clinic::ProcedureRoom::Request
    500.times do
      n = rng.rand(13)
      reqs = Array.new(n) do |i|
        s = rng.rand(0..20) * 15
        r.new(id: i, patient_id: rng.rand(1 + n / 2), start: s, finish: s + 15 * rng.rand(1..4), value: rng.rand(0..9))
      end
      puts outcome { Clinic::ProcedureRoom.best_total(reqs) }
    end
  },
  "RB6-time" => lambda {
    rng = Random.new(8)
    r = Clinic::ProcedureRoom::Request
    reqs = []
    12.times { |p| 4.times { s = rng.rand(480..1000); reqs << r.new(id: reqs.size, patient_id: p, start: s, finish: s + rng.rand(20..90), value: rng.rand(1..20)) } }
    (12...24).each { |p| s = rng.rand(480..1000); reqs << r.new(id: reqs.size, patient_id: p, start: s, finish: s + rng.rand(20..90), value: rng.rand(1..20)) }
    total = nil
    puts format("60 requests, 12 patients with alternatives: %.2f s (total %s)", clock { total = Clinic::ProcedureRoom.best_total(reqs.shuffle(random: rng)) }, total)
  },
  "RB7" => lambda {
    puts Digest::SHA256.hexdigest((0..Clinic::Pediatrics::MAX_AGE_DAYS).map { |a| Clinic::Pediatrics.band_for(a).inspect }.join("\n"))
    [364, 365, 366, 367, 0, 54_750].each { |a| puts outcome { Clinic::Pediatrics.band_for(a) } }
    [-1, 54_751, 3.0, "5", nil, 2**70].each { |a| puts outcome { Clinic::Pediatrics.band_for(a) } }
  },
  "RB8" => lambda {
    rng = Random.new(9)
    p = Clinic::Triage::Patient
    100.times do
      w = Array.new(rng.rand(60)) { |i| p.new(id: i, acuity: rng.rand(1..4), arrived_at: i) }
      puts outcome { Clinic::Triage.queue_order(w).map(&:id) }
    end
    w = Array.new(3000) { |i| p.new(id: i, acuity: rng.rand(1..5), arrived_at: i) }
    puts outcome { Digest::SHA256.hexdigest(Clinic::Triage.queue_order(w).map(&:id).join(",")) }
  },
  "RB8-time" => lambda {
    rng = Random.new(10)
    w = Array.new(5000) { |i| Clinic::Triage::Patient.new(id: i, acuity: rng.rand(1..5), arrived_at: i) }
    puts format("5,000 waiting: %.3f s", clock { Clinic::Triage.queue_order(w) })
  },
  "RB9" => lambda {
    rng = Random.new(11)
    100.times do
      a = Array.new(rng.rand(30)) { rng.rand(10) }
      b = Array.new(rng.rand(10)) { rng.rand(10) }
      puts outcome { Clinic::Pharmacy.undispensed(a, b) }
    end
  },
  "RB10" => lambda {
    rng = Random.new(10)
    300.times do
      a = rng.bytes(rng.rand(40))
      b = rng.rand(3).zero? ? rng.bytes(rng.rand(40)) : a.dup
      if !b.empty? && rng.rand(2).zero?
        i = rng.rand(b.bytesize)
        b.setbyte(i, b.getbyte(i) ^ (1 + rng.rand(255)))
      end
      puts outcome { Clinic::LabCallbacks.signature_matches?(a, b) }
    end
    puts outcome { Clinic::LabCallbacks.signature_matches?("\x01".b, nil) }
    puts outcome { Clinic::LabCallbacks.signature_matches?("".b, "".b) }
  },
  # Prints "same time" when a mismatch in the first byte takes as long as one in the last byte, else "timing leak".
  "RB10-leak" => lambda {
    n = 1 << 20
    a = Random.new(110).bytes(n)
    first = a.dup
    first.setbyte(0, first.getbyte(0) ^ 1)
    last = a.dup
    last.setbyte(n - 1, last.getbyte(n - 1) ^ 1)
    tf = []
    tl = []
    9.times do
      tf << clock { Clinic::LabCallbacks.signature_matches?(a, first) }
      tl << clock { Clinic::LabCallbacks.signature_matches?(a, last) }
    end
    puts tf.sort[4] * 4 < tl.sort[4] ? "timing leak" : "same time"
  },
  "RB11" => lambda {
    rng = Random.new(111)
    s = Clinic::AnalyzerBatch::Sample
    300.times do
      pending = Array.new(rng.rand(13)) { |i| s.new(sample_id: i, patient_id: rng.rand(5), reagent_ul: rng.rand(31), urgency: rng.rand(26) - 5) }
      cap = rng.rand(84) - 4
      puts outcome { Clinic::AnalyzerBatch.best_urgency(pending, cap) }
    end
    puts outcome { Clinic::AnalyzerBatch.best_urgency([], 100) }
    puts outcome { Clinic::AnalyzerBatch.best_urgency([s.new(sample_id: 1, patient_id: 1, reagent_ul: 0, urgency: 5), s.new(sample_id: 2, patient_id: 1, reagent_ul: 0, urgency: 7)], 0) }
    puts outcome { Clinic::AnalyzerBatch.best_urgency([s.new(sample_id: 1, patient_id: 1, reagent_ul: 0, urgency: 5)], -1) }
  },
  "RB11-time" => lambda {
    rng = Random.new(1110)
    s = Clinic::AnalyzerBatch::Sample
    pending = Array.new(90) { |i| s.new(sample_id: i, patient_id: rng.rand(70), reagent_ul: 10 + rng.rand(60), urgency: rng.rand(100)) }
    r = nil
    t = clock { r = Clinic::AnalyzerBatch.best_urgency(pending, 2_500) }
    puts format("90 samples, 2,500 uL: %.2f s (urgency %d)", t, r)
  },
  "RB12" => lambda {
    rng = Random.new(12)
    200.times do
      vials = Array.new(rng.rand(30)) { rng.rand(12) * 50 }
      copy = vials.dup
      dose = rng.rand(30) * 50
      dose = dose.to_f if rng.rand(3).zero?
      r = outcome { Clinic::Compounding.three_vial_fills(vials, dose) }
      puts vials == copy ? r : "#{r} INPUT CHANGED: #{vials.inspect}"
    end
    puts outcome { Clinic::Compounding.three_vial_fills([100, 200, 300, 250, 350], 600.0) }
    puts outcome { Clinic::Compounding.three_vial_fills([100, 200, 300], 600.5) }
    puts outcome { Clinic::Compounding.three_vial_fills(Array.new(40, 7), 21) }
    puts outcome { Clinic::Compounding.three_vial_fills([10**20, 10**20, 1, 2], 2 * 10**20 + 1) }
  },
  "RB12-time" => lambda {
    rng = Random.new(120)
    vials = Array.new(1_000) { 50 * (1 + rng.rand(400)) }
    r = nil
    t = clock { r = Clinic::Compounding.three_vial_fills(vials, 30_000) }
    puts format("1,000 vials: %.2f s (%d fills)", t, r)
  },
  "RBW1" => lambda {
    unless File.exist?("lib/clinic/lab_alerts.rb")
      puts "no lib/clinic/lab_alerts.rb"
      next
    end
    require "clinic/lab_alerts"
    result = Struct.new(:id, :patient_id, :test_code, :taken_on)
    rng = Random.new(12)
    mismatches = 0
    300.times do |t|
      n = rng.rand(40)
      base = Date.new(2026, 1, 1)
      results = Array.new(n) { |i| result.new(i, rng.rand(4), %w[HB GLU].sample(random: rng), base + rng.rand(60)) }
      window = rng.rand(0..12)
      expected = results.each_with_index.select do |r, i|
        results.first(i).any? { |e| e.patient_id == r.patient_id && e.test_code == r.test_code && (e.taken_on - r.taken_on).abs <= window }
      end.map(&:first).map(&:id)
      got = begin
        Clinic::LabAlerts.repeat_tests(results, window).map(&:id)
      rescue StandardError => e
        "raises #{e.class}"
      end
      next if got == expected

      mismatches += 1
      puts "mismatch (case #{t}, window #{window}): expected #{expected.inspect}, got #{got.inspect}" if mismatches <= 3
    end
    big = Array.new(500_000) { |i| result.new(i, rng.rand(100_000), %w[HB GLU K NA CRP].sample(random: rng), Date.new(2026, 1, 1) + rng.rand(365)) }
    seconds = clock { Clinic::LabAlerts.repeat_tests(big, 30) }
    puts format("#{mismatches} mismatches in 300 cases; 500,000 results in %.2f s", seconds)
  }
}.freeze

CHECKS.fetch(ARGV[0]).call
