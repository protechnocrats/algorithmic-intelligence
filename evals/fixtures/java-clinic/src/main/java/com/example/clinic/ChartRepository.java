package com.example.clinic;

import java.util.HashMap;
import java.util.Map;

/**
 * Charts for one chart-viewer request. Each request gets its own repository, so a
 * chart is loaded from the store at most once per request.
 */
public final class ChartRepository {
    private final ChartStore store;
    private final Map<Long, Chart> loaded = new HashMap<>();

    public ChartRepository(ChartStore store) {
        this.store = store;
    }

    public Chart chart(long chartId) {
        return loaded.computeIfAbsent(chartId, store::load);
    }
}
