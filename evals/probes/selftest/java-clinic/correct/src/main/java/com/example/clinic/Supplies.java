package com.example.clinic;

import java.util.ArrayList;
import java.util.List;

/** Supply orders for wards. */
public final class Supplies {
    private Supplies() {}

    /** The items of an order that the ward does not stock, in order, with repeats kept. Item codes come from the hospital's own catalog. */
    public static List<String> notStocked(List<String> orderItems, List<String> wardStock) {
        List<String> missing = new ArrayList<>();
        java.util.Set<String> stock = new java.util.HashSet<>(wardStock);
        for (String item : orderItems) {
            if (!stock.contains(item)) missing.add(item);
        }
        return missing;
    }
}
