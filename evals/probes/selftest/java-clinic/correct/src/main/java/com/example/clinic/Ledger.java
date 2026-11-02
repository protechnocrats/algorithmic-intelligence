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
        for (int i = 0; i < ranges.size(); i++) {
            Range r = ranges.get(i);
            if (r.from() < 0 || r.to() > amounts.length || r.from() > r.to()) {
                throw new IllegalArgumentException("range " + r + " is outside the ledger");
            }
        }
        Integer[] order = new Integer[ranges.size()];
        for (int i = 0; i < order.length; i++) order[i] = i;
        java.util.Arrays.sort(order, (x, y) -> ranges.get(x).from() != ranges.get(y).from()
                ? Integer.compare(ranges.get(x).from(), ranges.get(y).from()) : Integer.compare(ranges.get(x).to(), ranges.get(y).to()));
        int k = 0;
        while (k < order.length) {
            int from = ranges.get(order[k]).from(), j = from;
            double total = 0;
            for (; k < order.length && ranges.get(order[k]).from() == from; k++) {
                for (; j < ranges.get(order[k]).to(); j++) total += amounts[j];
                totals[order[k]] = total;
            }
        }
        return totals;
    }
}
