# frozen_string_literal: true

module Clinic
  # Wrong: String#== stops at the first differing byte, so the time reveals how much of a forged signature is right.
  module LabCallbacks
    def self.signature_matches?(computed, received)
      !received.nil? && computed == received
    end
  end
end
