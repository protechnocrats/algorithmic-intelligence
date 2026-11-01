package com.example.shop

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.Clock
import java.time.Instant
import java.time.ZoneOffset

class ShopTest {

    @Test
    fun pluginReportsRunRegisteredPlugins() {
        val customers = listOf(Customer("c2", "B", 1), Customer("c1", "A", 1), Customer("c3", "C", 1))
        val orders = listOf(Order("o1", "c1", 500))
        assertEquals(listOf("c2", "c3"), runReportPlugins(orders, customers)["dormant-customers"])
    }

    @Test
    fun blockedUsersKeepsUserOrder() {
        val users = listOf(User("3", "C"), User("1", "A"), User("2", "B"))
        assertEquals(listOf(User("3", "C"), User("2", "B")), blockedUsers(users, listOf("2", "3")))
    }

    @Test
    fun countsPeriodsWithZeroNetChange() {
        assertEquals(4, countPeriodsWithNetChange(intArrayOf(1, -1, 1, -1), target = 0))
    }

    @Test
    fun uniqueTagsInFirstSeenOrder() {
        val posts = listOf(Post("p1", listOf("b", "a")), Post("p2", listOf("a", "c", "b")))
        assertEquals(listOf("b", "a", "c"), uniqueTags(posts))
    }

    @Test
    fun medianOfOddLength() {
        assertEquals(3.0, median(intArrayOf(1, 3, 9)), 0.0)
    }

    @Test
    fun categoryNamesParentFirst() {
        val tree = Category("root", listOf(Category("a", listOf(Category("a1"))), Category("b")))
        assertEquals(listOf("root", "a", "a1", "b"), allCategoryNames(tree))
    }

    @Test
    fun eveningSurcharge() {
        val evening = Clock.fixed(Instant.parse("2026-01-01T18:00:00Z"), ZoneOffset.UTC)
        val morning = Clock.fixed(Instant.parse("2026-01-01T09:00:00Z"), ZoneOffset.UTC)
        assertEquals(132, ShippingCalculator(evening).quote(1000, "zone-a"))
        assertEquals(120, ShippingCalculator(morning).quote(1000, "zone-a"))
    }

    @Test
    fun tokens() {
        assertTrue(tokensMatch("abc123", "abc123"))
        assertFalse(tokensMatch("abc124", "abc123"))
        assertFalse(tokensMatch("abc12", "abc123"))
    }

    @Test
    fun namesForOrders() {
        val repo = InMemoryCustomerRepository(listOf(Customer("c1", "Ada", 10)))
        val names = OrderSummaryService(repo).customerNamesForOrders(
            listOf(Order("o1", "c1", 500), Order("o2", "gone", 100)),
        )
        assertEquals(listOf("Ada", "Unknown"), names)
    }

    @Test
    fun hops() {
        val graph = mapOf("a" to listOf("b", "c"), "b" to listOf("d"), "c" to listOf("d"), "d" to emptyList())
        assertEquals(2, shortestHops(graph, "a", "d"))
        assertEquals(-1, shortestHops(graph, "d", "a"))
    }

    @Test
    fun topSellersHighestFirst() {
        val products = listOf(Product("s1", "A", 5), Product("s2", "B", 9), Product("s3", "C", 7))
        assertEquals(listOf("s2", "s3"), topSellers(products, 2).map { it.sku })
    }

    @Test
    fun workingDays() {
        assertEquals(listOf("Mon", "Tue", "Wed", "Thu", "Fri"), workingDayLabels())
    }

    @Test
    fun crateValue() {
        val items = listOf(CrateItem("a", 5, 10), CrateItem("b", 4, 40), CrateItem("c", 6, 30), CrateItem("d", 3, 50))
        assertEquals(90L, maxCrateValue(items, capacityKg = 10))
    }

    @Test
    fun bundles() {
        assertEquals(2L, countBundles(intArrayOf(100, 200, 300, 400, 500), budgetCents = 900))
    }
}
