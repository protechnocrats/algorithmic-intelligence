package com.example.clinic;

import java.util.List;
import java.util.*;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Turns the raw test codes in incoming lab results into display labels. Shared by
 * all ingestion threads. The terminology is replaced on the first of each month by
 * {@link #reload}, while ingestion keeps running; labels must use the new
 * terminology from the moment reload returns.
 */
public final class CodeFormatter {
    private final Map<String, String> memo = new java.util.concurrent.ConcurrentHashMap<>();
    private volatile List<Term> terminology;

    public CodeFormatter(List<Term> terminology) {
        this.terminology = List.copyOf(terminology);
    }

    public void reload(List<Term> newTerminology) {
        this.terminology = List.copyOf(newTerminology);
    }

    /**
     * "LAB 2345-7 Glucose" for a raw code that normalizes to a known term, and
     * "UNKNOWN &lt;raw&gt;" otherwise. Raw codes arrive as free text, for example
     * " lab:2345 7 " or "Lab-2345-7".
     */
    public String label(String rawCode) {
        return memo.computeIfAbsent(rawCode, this::compute);
    }

    private String compute(String rawCode) {
        Matcher m = Pattern.compile("^\\s*([A-Za-z]+)[:\\s-]*(\\d{1,7})[\\s-]?(\\d)\\s*$").matcher(rawCode);
        if (m.matches()) {
            String normalized = m.group(1).toUpperCase(Locale.ROOT) + " " + m.group(2) + "-" + m.group(3);
            for (Term term : terminology) {
                if (term.code().equals(normalized)) {
                    return term.code() + " " + term.shortName();
                }
            }
        }
        return "UNKNOWN " + rawCode.strip();
    }
}
