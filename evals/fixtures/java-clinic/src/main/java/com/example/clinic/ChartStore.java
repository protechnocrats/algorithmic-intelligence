package com.example.clinic;

/** The chart database. One query per call (about 3 ms). */
public interface ChartStore {
    Chart load(long chartId);
}
