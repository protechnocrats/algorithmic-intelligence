# frozen_string_literal: true

require "openssl"

module Clinic
  # Correct: OpenSSL.fixed_length_secure_compare takes the same time wherever equal-length strings differ.
  module LabCallbacks
    def self.signature_matches?(computed, received)
      return false if received.nil? || computed.bytesize != received.bytesize

      OpenSSL.fixed_length_secure_compare(computed, received)
    end
  end
end
