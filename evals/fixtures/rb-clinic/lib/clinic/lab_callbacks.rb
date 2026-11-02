# frozen_string_literal: true

module Clinic
  # Callbacks from partner labs. Each callback carries an HMAC-SHA256 signature
  # that we recompute with the partner's shared secret before accepting the results.
  module LabCallbacks
    # True when the signature that came with a callback equals the one we computed.
    # Runs once per callback (see VOLUMES).
    def self.signature_matches?(computed, received)
      return false if received.nil? || computed.bytesize != received.bytesize

      diff = 0
      computed.bytes.zip(received.bytes) { |a, b| diff |= a ^ b }
      diff.zero?
    end
  end
end
