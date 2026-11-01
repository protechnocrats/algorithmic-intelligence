package com.example.shop

/** IDs of customers with no orders in the period, in customer order. */
class DormantCustomersReport : ReportPlugin {
    override val name = "dormant-customers"

    override fun run(orders: List<Order>, customers: List<Customer>): List<String> =
        customers.filter { customer -> orders.none { it.customerId == customer.id } }.map { it.id }
}
