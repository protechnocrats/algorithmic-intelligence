package com.example.shop

/** Typical production volumes, from the operations runbook. */
object Volumes {
    const val USERS_PER_MODERATION_RUN = 250_000
    const val BLOCKED_IDS = 40_000
    const val LEDGER_DAYS_PER_AUDIT = 20_000
    const val POSTS_PER_TAG_INDEX = 100_000
    const val ORDERS_PER_REPORT = 300_000
    const val CUSTOMERS = 120_000
    const val CATALOG_PRODUCTS = 1_000_000
    const val PARCELS_PER_BATCH = 50_000
    const val WAREHOUSE_STATIONS = 80_000
    const val ITEMS_PER_CRATE_PLAN = 80
    const val CRATE_CAPACITY_KG = 1_500
    const val PRODUCTS_PER_BUNDLE_SEARCH = 4_000
}

class NightlyJobs(
    private val summaries: OrderSummaryService,
    private val shipping: ShippingCalculator,
) {
    fun moderation(users: List<User>, blockedIds: List<String>) = blockedUsers(users, blockedIds)

    fun ledgerAudit(deltas: IntArray) = countPeriodsWithNetChange(deltas, target = 0)

    fun tagIndex(posts: List<Post>) = uniqueTags(posts)

    fun activityReport(orders: List<Order>, customers: List<Customer>, cutoffDay: Int) =
        ordersFromActiveCustomers(orders, customers, cutoffDay)

    fun invoiceNames(orders: List<Order>) = summaries.customerNamesForOrders(orders)

    fun dashboardTopSellers(catalog: List<Product>) = topSellers(catalog, k = 10)

    fun shippingBatch(parcels: List<Pair<Int, String>>) = shipping.quoteAll(parcels)

    /** Supplier feeds can nest categories deeply. */
    fun importCategories(root: Category) = allCategoryNames(root)

    fun routing(adjacency: Map<String, List<String>>, from: String, to: String) =
        shortestHops(adjacency, from, to)

    fun cratePlanning(items: List<CrateItem>) = maxCrateValue(items, Volumes.CRATE_CAPACITY_KG)

    fun bundleSuggestions(pricesCents: IntArray, budgetCents: Long) = countBundles(pricesCents, budgetCents)

    fun pluginReports(orders: List<Order>, customers: List<Customer>) = runReportPlugins(orders, customers)
}
