# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 3
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Time**: 347.3092s (actual wall-clock execution time)
- **Time from Analysis**: 1560.4477s (sum of all profiled sections)

*Note: These times may differ due to profiling overhead and untracked code sections.*

## Component Breakdown

| Component | Time (s) | Calls | Avg Time (ms) | % of Total |
|-----------|----------|-------|---------------|------------|
| ResPlaN | 395.7127 | 196460 | 2.01 | 25.4% |
| CBS | 751.9016 | 263301 | 2.86 | 48.2% |
| SIPPS | 412.8326 | 8258336 | 0.05 | 26.5% |

## Top 5 Time-Consuming Functions

| Function | Calls | Total Time (s) | Avg Time (ms) |
|----------|-------|----------------|---------------|
| resplan_iteration | 63542 | 346.2784 | 5.45 |
| compute_plan_cbs | 25562 | 289.9390 | 11.34 |
| low_level_search_cbs | 100411 | 285.8629 | 2.85 |
| CBS_iteration | 47425 | 173.9871 | 3.67 |
| build_safe_interval_table | 100411 | 156.0271 | 1.55 |

## Performance Notes

**Note on `low_level_search_cbs`**: This function is called from multiple contexts:
- During root CBS initialization (~15-20% of calls)
- During CBS conflict resolution iterations (~80-85% of calls)
The time reported includes ALL calls aggregated across both contexts.

## Detailed Granular Statistics

<pre style="overflow-x: auto; white-space: pre;">
ResPlaN | Component: ResPlaN | Total: 347.3092s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 63542 | Total: 346.2784s | Avg: 5.45ms | % of Parent: 99.7%
    └─ compute_plan_cbs | Component: CBS | Calls: 25562 | Total: 289.9390s | Avg: 11.34ms | % of Parent: 83.7%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0051s | Avg: 5.10ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 23701 | Total: 115.4346s | Avg: 4.87ms | % of Parent: 39.8%
      └─ cbs_iteration | Component: CBS | Calls: 47425 | Total: 173.9871s | Avg: 3.67ms | % of Parent: 60.0%
        └─ cbs_vertex_conflict | Component: CBS | Calls: 58 | Total: 0.7606s | Avg: 13.11ms | % of Parent: 0.4%
        └─ build_solution | Component: CBS | Calls: 47425 | Total: 0.8222s | Avg: 0.02ms | % of Parent: 0.5%
        └─ detect_conflict | Component: CBS | Calls: 42419 | Total: 0.5247s | Avg: 0.01ms | % of Parent: 0.3%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 63542 | Total: 0.0994s | Avg: 0.00ms | % of Parent: 0.0%
    └─ macroaction_loop | Component: ResPlaN | Calls: 7661 | Total: 0.6391s | Avg: 0.08ms | % of Parent: 0.2%
    └─ rcheck | Component: ResPlaN | Calls: 61715 | Total: 48.6958s | Avg: 0.79ms | % of Parent: 14.1%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Total: 0.0000s | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-04-28 12:43:06*