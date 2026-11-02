# frozen_string_literal: true

module Clinic
  VisitLine = Struct.new(:code, :service_date, :quantity, keyword_init: true)
  StatementLine = Struct.new(:code, :service_date, :quantity, :unit_price_cents, :total_cents, keyword_init: true)

  class UnknownCode < StandardError; end
  class NoPriceOnDate < StandardError; end

  # Prices the lines of patient statements.
  class Billing
    # prices: a PriceClient (see price_client.rb).
    def initialize(prices)
      @prices = prices
    end

    # One statement line per visit line, in order. Raises UnknownCode or
    # NoPriceOnDate, as PriceClient#price_on does, for the first line that cannot be priced.
    def statement_lines(visit_lines)
      histories = {}
      visit_lines.map do |line|
        changes = histories[line.code] ||= @prices.price_history(line.code)
        i = changes.bsearch_index { |from, _| from > line.service_date } || changes.size
        raise NoPriceOnDate, "#{line.code} #{line.service_date}" if i.zero?

        unit = changes[i - 1][1]
        StatementLine.new(code: line.code, service_date: line.service_date, quantity: line.quantity,
                          unit_price_cents: unit, total_cents: unit * line.quantity)
      end
    end
  end
end
