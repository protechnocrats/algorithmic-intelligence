package com.example.clinic;

import java.util.ArrayList;
import java.util.List;

/** Supply orders for wards. */
public final class Supplies {
    private Supplies() {}

    /** The items of an order that the ward does not stock, in order, with repeats kept. Item codes come from the hospital's own catalog. */
    public static List<String> notStocked(List<String> orderItems, List<String> wardStock) {
        List<String> missing = new ArrayList<>();
        for (String item : orderItems) {
            if (!wardStock.contains(item)) missing.add(item);
        }
        return missing;
    }
}
