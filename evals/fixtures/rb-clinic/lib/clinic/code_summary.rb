module Clinic
  # The code summary page: one row per billed code, with its display name.
  module CodeSummary
    # rows: [code, count, discontinued] triples. Returns [display name, count] pairs.
    def self.rows(rows, labels)
      rows.map do |code, count, discontinued|
        name = labels.display_name(code)
        name << " (discontinued)" if discontinued
        [name, count]
      end
    end
  end
end
