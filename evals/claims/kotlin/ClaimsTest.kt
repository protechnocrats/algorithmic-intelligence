// Checks the claims in skills/complexity-optimizer/languages/KOTLIN.md that the
// official documentation does not settle, plus the ones already confirmed by a run.
// Each check prints one "CLAIM <id> ..." line with the observed value, then asserts
// the value the skill file states. A failure means the skill file is wrong.
// Run with evals/claims/kotlin-claims.sh.
package claims

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

data class Point(val x: Double)

private fun mutateFirst(vararg xs: Int) { xs[0] = 99 }

class ClaimsTest {
    private fun claim(id: String, text: String, observed: Any?, expected: Any?) {
        println("CLAIM $id ${if (observed == expected) "OK  " else "FAIL"} $text: observed=$observed expected=$expected")
        assertEquals("$id: $text", expected, observed)
    }

    // Pending: not stated in the docs (2026-10-31). Update KOTLIN.md from these results.

    @Test fun arrayDequeAcceptsNull() {
        val d = ArrayDeque<String?>()
        val ok = runCatching { d.addLast(null); d.addFirst(null); d.removeFirst() == null && d.size == 1 }.getOrDefault(false)
        claim("K-P1", "kotlin.collections.ArrayDeque accepts null", ok, true)
    }

    @Test fun dataClassDoubleZero() =
        claim("K-P2", "Point(0.0) == Point(-0.0)", Point(0.0) == Point(-0.0), false)

    @Test fun dataClassDoubleNaN() =
        claim("K-P3", "Point(NaN) == Point(NaN)", Point(Double.NaN) == Point(Double.NaN), true)

    @Test fun spreadCopiesArray() {
        val a = intArrayOf(1, 2)
        mutateFirst(*a)
        claim("K-P4", "foo(*array) passes a copy (caller's array unchanged)", a[0] == 1, true)
    }

    @Test fun longShiftUsesSixBits() =
        claim("K-P5", "1L shl 64 == 1L", (1L shl 64) == 1L, true)

    @Test fun removeAllPredicateIsLinear() {
        val ratio = growth { n -> (0 until n).toMutableList().also { it.removeAll { x -> x % 2 == 0 } } }
        println("CLAIM K-P6 ${if (ratio < 3.0) "OK  " else "FAIL"} ArrayList.removeAll { } is O(n): time ratio per doubling=${"%.2f".format(ratio)} (linear ~2, quadratic ~4)")
        assertTrue("K-P6: removeAll { } grows faster than linear (ratio $ratio)", ratio < 3.0)
    }

    // Confirmed on Kotlin 2.4.10 (2026-10-31); kept as regression checks.

    @Test fun floatingPointEquality() {
        val nan = Double.NaN
        claim("K-C1", "IEEE NaN == NaN for static Double", nan == nan, false)
        claim("K-C2", "IEEE -0.0 == 0.0 for static Double", -0.0 == 0.0, true)
        claim("K-C3", "setOf(NaN).contains(NaN)", setOf(nan).contains(Double.NaN), true)
        claim("K-C4", "listOf(-0.0).contains(0.0)", listOf(-0.0).contains(0.0), false)
    }

    @Test fun arraysCompareByReference() {
        data class Box(val a: IntArray)
        claim("K-C5", "data class with IntArray: equal contents are equal", Box(intArrayOf(1)) == Box(intArrayOf(1)), false)
    }

    @Test fun splitKeepsTrailingEmpties() =
        claim("K-C6", "\"a,b,,\".split(\",\")", "a,b,,".split(","), listOf("a", "b", "", ""))

    @Test fun exceptionTypes() {
        fun name(f: () -> Unit) = runCatching(f).exceptionOrNull()?.javaClass?.simpleName
        claim("K-C7", "first { } on no match", name { listOf(1).first { it == 2 } }, "NoSuchElementException")
        claim("K-C8", "map[k]!! on missing key", name { mapOf(1 to 1)[2]!! }, "NullPointerException")
        claim("K-C9", "getValue on missing key", name { mapOf(1 to 1).getValue(2) }, "NoSuchElementException")
    }

    @Test fun extremesAndNaN() {
        val pairs = listOf(1 to "a", 1 to "b")
        claim("K-C10", "maxBy returns the first maximal element", pairs.maxBy { it.first }.second, "a")
        claim("K-C11", "sortedBy { }.last() returns the last maximal element", pairs.sortedBy { it.first }.last().second, "b")
        claim("K-C12", "maxOrNull with NaN", listOf(1.0, Double.NaN).maxOrNull()!!.isNaN(), true)
        claim("K-C13", "sorted() puts NaN last", listOf(Double.NaN, 1.0).sorted().last().isNaN(), true)
    }

    @Test fun remainderAndMod() {
        claim("K-C14", "-7 % 2", -7 % 2, -1)
        claim("K-C15", "(-7).mod(2)", (-7).mod(2), 1)
    }

    @Test fun listMinusListIsQuadratic() {
        val ratio = growth { n -> (0 until n).toList() - (n / 2 until n + n / 2).toList() }
        println("CLAIM K-C16 ${if (ratio > 3.0) "OK  " else "FAIL"} list - List is O(n·m): time ratio per doubling=${"%.2f".format(ratio)} (quadratic ~4)")
        assertTrue("K-C16: list - List no longer quadratic (ratio $ratio): update KOTLIN.md", ratio > 3.0)
    }

    // Median time ratio between sizes n and 2n, after warmup.
    private fun growth(work: (Int) -> Any): Double {
        fun time(n: Int): Double {
            repeat(3) { work(n) }
            return List(5) { val t = System.nanoTime(); work(n); (System.nanoTime() - t).toDouble() }.sorted()[2]
        }
        val sizes = listOf(20_000, 40_000, 80_000)
        val times = sizes.map(::time)
        return listOf(times[1] / times[0], times[2] / times[1]).sorted()[0]
    }
}
