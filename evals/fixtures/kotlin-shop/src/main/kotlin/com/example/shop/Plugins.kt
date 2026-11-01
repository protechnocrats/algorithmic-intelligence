package com.example.shop

import java.util.ServiceLoader

/** A report that runs with the nightly jobs. Register implementations in META-INF/services. */
interface ReportPlugin {
    val name: String

    fun run(orders: List<Order>, customers: List<Customer>): List<String>
}

/** Runs every registered report plugin, keyed by plugin name. */
fun runReportPlugins(orders: List<Order>, customers: List<Customer>): Map<String, List<String>> =
    ServiceLoader.load(ReportPlugin::class.java).associate { it.name to it.run(orders, customers) }
