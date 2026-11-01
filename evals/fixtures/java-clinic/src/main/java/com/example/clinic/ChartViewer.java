package com.example.clinic;

import java.util.ArrayList;
import java.util.List;

/** Assembles the panels of the chart viewer. */
public final class ChartViewer {
    private ChartViewer() {}

    /** The latest entry of each requested chart, in request order (a chart may be requested by several panels). */
    public static List<String> latestEntries(ChartRepository repository, List<Long> panelChartIds) {
        List<String> latest = new ArrayList<>();
        for (long chartId : panelChartIds) {
            List<String> entries = repository.chart(chartId).entries();
            latest.add(entries.isEmpty() ? "" : entries.get(entries.size() - 1));
        }
        return latest;
    }
}
