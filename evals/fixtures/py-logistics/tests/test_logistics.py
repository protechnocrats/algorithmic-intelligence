import threading
import time
import unittest
from datetime import date

from logistics.bulk import repeated_ids
from logistics.business_days import business_days_between, observed_holidays
from logistics.depots import nearest_depot
from logistics.manifest import unmatched_parcels
from logistics.profit import best_operating_plan
from logistics.quotes import QuoteBook, Shipment


class FakeCarrier:
    """Stands in for CarrierClient: a short delay per call, like a network request."""

    def __init__(self, delay=0.002):
        self.delay = delay
        self.calls = []
        self._lock = threading.Lock()

    def quote(self, shipment_id, lanes):
        time.sleep(self.delay)
        with self._lock:
            self.calls.append((shipment_id, tuple(lanes)))
        return 100 * len(lanes)


class ProfitTest(unittest.TestCase):
    def test_without_closures(self):
        self.assertEqual(best_operating_plan([3, -1, 4], 0, 2), 6)
        self.assertEqual(best_operating_plan([-3, -1, -4], 0, 2), -1)

    def test_closing_a_bad_day(self):
        self.assertEqual(best_operating_plan([5, -10, 6, 2], 1, 1), 12)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            best_operating_plan([], 1, 0)
        with self.assertRaises(ValueError):
            best_operating_plan([1], -1, 0)


class QuotesTest(unittest.TestCase):
    def test_quotes_in_shipment_order(self):
        carrier = FakeCarrier()
        book = QuoteBook(carrier)
        shipments = [Shipment("s1", ("A", "B", "A")), Shipment("s2", ("C",)), Shipment("s3", ("D", "E"))]
        self.assertEqual(book.quote_all(shipments), {"s1": 200, "s2": 100, "s3": 200})
        self.assertEqual(book.requests_made, 3)
        self.assertIn(("s1", ("A", "B")), carrier.calls)


class BusinessDaysTest(unittest.TestCase):
    def test_week_without_holidays(self):
        self.assertEqual(business_days_between(date(2024, 3, 4), date(2024, 3, 11)), 5)

    def test_holiday_on_a_weekday(self):
        self.assertEqual(business_days_between(date(2024, 7, 1), date(2024, 7, 8)), 4)

    def test_saturday_holiday_observed_on_friday(self):
        self.assertIn(date(2020, 7, 3), observed_holidays(2020))

    def test_empty_and_reversed_ranges(self):
        self.assertEqual(business_days_between(date(2024, 3, 4), date(2024, 3, 4)), 0)
        self.assertEqual(business_days_between(date(2024, 3, 11), date(2024, 3, 4)), 0)

    def test_unsupported_dates(self):
        with self.assertRaises(ValueError):
            business_days_between(date(1999, 12, 31), date(2000, 1, 5))


class DepotsTest(unittest.TestCase):
    def test_nearest(self):
        self.assertEqual(nearest_depot(47.6, -122.3), "SEA")
        self.assertEqual(nearest_depot(40.7, -74.0), "JFK")
        self.assertEqual(nearest_depot(29.76, -95.37), "DFW")


class BulkTest(unittest.TestCase):
    def test_repeated_ids(self):
        self.assertEqual(repeated_ids([5, 3, 5, 9, 3, 3]), [3, 5])
        self.assertEqual(repeated_ids([1, 2, 3]), [])
        self.assertEqual(repeated_ids([]), [])


class ManifestTest(unittest.TestCase):
    def test_unmatched_parcels(self):
        self.assertEqual(unmatched_parcels(["a", "x", "b", "x"], ["a", "b"]), ["x", "x"])


if __name__ == "__main__":
    unittest.main()
