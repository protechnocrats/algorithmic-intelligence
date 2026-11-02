# frozen_string_literal: true

require "yaml"

module Clinic
  # Display names for billing codes, from config/labels.yml. Administrators edit
  # that file on the production servers; an edit takes effect on the next call,
  # without a restart.
  class Labels
    def initialize(path)
      @path = path
    end

    def display_name(code)
      @names ||= YAML.safe_load_file(@path)
      @names.fetch(code) { "Unlisted (#{code})" }
    end
  end
end
