# frozen_string_literal: true

require "date"
require "json"
require "net/http"

module Clinic
  # Client for the pricing service. Every method is one HTTPS round trip
  # (about 2 ms at p50). A code's price changes on effective dates; each price
  # applies from its effective date until the next change.
  class PriceClient
    def initialize(base_url)
      @base = URI(base_url)
    end

    # The price in cents in effect on date. Raises UnknownCode for a code the
    # service does not know, and NoPriceOnDate for a date before the code's first price.
    def price_on(code, date)
      body = get("/prices/#{URI.encode_www_form_component(code)}/on/#{date.iso8601}")
      body.fetch("cents")
    end

    # The prices in cents in effect today, for up to 200 codes. Unknown codes are left out.
    def current_prices(codes)
      raise ArgumentError, "at most 200 codes" if codes.size > 200

      get("/prices/current?codes=#{codes.map { |c| URI.encode_www_form_component(c) }.join(',')}")
        .transform_values { |v| v.fetch("cents") }
    end

    # Every price change for the code as [effective_date, cents] pairs, oldest
    # first. Raises UnknownCode for a code the service does not know.
    def price_history(code)
      get("/prices/#{URI.encode_www_form_component(code)}/history").map { |c| [Date.iso8601(c["from"]), c["cents"]] }
    end

    private

    def get(path)
      response = Net::HTTP.get_response(URI.join(@base, path))
      case response
      when Net::HTTPNotFound then raise UnknownCode, path
      when Net::HTTPUnprocessableEntity then raise NoPriceOnDate, path
      end
      response.value
      JSON.parse(response.body)
    end
  end
end
