"""Typical production volumes, from the operations runbook."""

VOLUMES = {
    "depots_reporting_profit": 400,
    "days_of_profit_history": 3_650,
    "max_closures_per_plan": 3,
    "shipments_per_quote_batch": 5_000,
    "stops_per_shipment_max": 6,
    "quote_workers": 8,
    "carrier_quote_latency_ms": 40,
    "sla_checks_per_night": 2_000_000,
    "sla_window_days_max": 30,
    "depots_in_network": 12,
    "orders_routed_per_night": 2_000_000,
    "ids_per_bulk_request_max": 100_000,
    "parcels_scanned_per_truck": 50_000,
    "parcels_on_manifest": 50_000,
    "deliveries_per_driver_per_quarter": 4_000,
}
