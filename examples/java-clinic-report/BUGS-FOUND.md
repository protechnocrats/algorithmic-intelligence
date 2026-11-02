# Bugs found

No bug was fixed. One edge behavior was reproduced; whether it is a bug or a contract question is unclear, so it is recorded here and not treated as a bug (rule 4).

### BUG-1. Null elements in a partner upload throw NPE at position-dependent points

- **Location:** `src/main/java/com/example/clinic/PartnerImport.java:14` (`repeatedVisits`, inner loop `:19`)
- **What happens:** Reproduced by running the original code in a scratch program:
  - `[VisitKey(1,1), null]` throws `NullPointerException`.
  - `[null, VisitKey(1,1)]` returns `[]`.
  - `[VisitKey(1,1), null, VisitKey(2,1)]` throws `NullPointerException`.
  - `[null, null]` throws `NullPointerException`.
  - `[VisitKey(1,1), VisitKey(1,1), null]` returns `[VisitKey(1,1)]`, by reading the code, not run.
- **Expected:** Unclear. The Javadoc does not say whether nulls are allowed. The class is documented as taking uploads straight from a partner's request body.
- **Impact:** Partner import requests containing null elements. Whether the parser can produce nulls is unknown.
- **Status:** Left as is. Any optimization that rewrites this function changes which inputs throw, so it is a known behavior change under rule 5 (BC-4 in `OPTIMIZATION-REPORT.md`), not a bug fix.
- **Suggested fix:** Not applied. Developer should decide whether nulls are allowed, then state the contract in the Javadoc.
