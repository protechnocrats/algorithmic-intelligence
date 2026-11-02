package com.example.clinic;

import java.util.List;

/** Statement totals over an account's ledger. */
public final class Ledger {
    private Ledger() {}

    /**
     * The total of {@code amounts} over each range, in the order given. Amounts are
     * the account's ledger entries in posting order, in dollars.
     *
     * @throws IllegalArgumentException for a range outside the ledger or with from after to
     */
    public static double[] rangeTotals(double[] amounts, List<Range> ranges) {
        double[] totals = new double[ranges.size()];
        double[] prefix = new double[amounts.length + 1];
        for (int i = 0; i < amounts.length; i++) prefix[i + 1] = prefix[i] + amounts[i];
        for (int i = 0; i < ranges.size(); i++) {
            Range r = ranges.get(i);
            if (r.from() < 0 || r.to() > amounts.length || r.from() > r.to()) {
                throw new IllegalArgumentException("range " + r + " is outside the ledger");
            }
            totals[i] = prefix[r.to()] - prefix[r.from()];
        }
        return totals;
    }
}
