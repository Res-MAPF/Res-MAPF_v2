# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 1
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Time**: 2300.7464s (actual wall-clock execution time)
- **Time from Analysis**: 10175.6658s (sum of all profiled sections)

*Note: These times may differ due to profiling overhead and untracked code sections.*

## Component Breakdown

| Component | Time (s) | Calls | Avg Time (ms) | % of Total |
|-----------|----------|-------|---------------|------------|
| ResPlaN | 2486.7928 | 816792 | 3.04 | 24.4% |
| CBS | 5216.9272 | 1105526 | 4.72 | 51.3% |
| SIPPS | 2471.9449 | 58431356 | 0.04 | 24.3% |

## Top 5 Time-Consuming Functions

| Function | Calls | Total Time (s) | Avg Time (ms) |
|----------|-------|----------------|---------------|
| resplan_iteration | 265021 | 2296.1897 | 8.66 |
| compute_plan_cbs | 105029 | 1905.7214 | 18.14 |
| low_level_search_cbs | 410354 | 1884.7588 | 4.59 |
| CBS_iteration | 202472 | 1419.5725 | 7.01 |
| build_safe_interval_table | 410354 | 1165.8372 | 2.84 |

## Performance Notes

**Note on `low_level_search_cbs`**: This function is called from multiple contexts:
- During root CBS initialization (~15-20% of calls)
- During CBS conflict resolution iterations (~80-85% of calls)
The time reported includes ALL calls aggregated across both contexts.

## Detailed Granular Statistics

<pre style="overflow-x: auto; white-space: pre;">
ResPlaN | Component: ResPlaN | Total: 2300.7464s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 265021 | Total: 2296.1897s | Avg: 8.66ms | % of Parent: 99.8%
    └─ compute_plan_cbs | Component: CBS | Calls: 105029 | Total: 1905.7214s | Avg: 18.14ms | % of Parent: 83.0%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0053s | Avg: 5.30ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 93628 | Total: 483.5277s | Avg: 5.16ms | % of Parent: 25.4%
      └─ cbs_iteration | Component: CBS | Calls: 202472 | Total: 1419.5725s | Avg: 7.01ms | % of Parent: 74.5%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 202472 | Total: 4.1127s | Avg: 0.02ms | % of Parent: 0.3%
        └─ detect_conflict | Component: CBS | Calls: 185198 | Total: 2.7565s | Avg: 0.01ms | % of Parent: 0.2%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 265021 | Total: 0.5112s | Avg: 0.00ms | % of Parent: 0.0%
    └─ macroaction_loop | Component: ResPlaN | Calls: 27383 | Total: 3.0215s | Avg: 0.11ms | % of Parent: 0.1%
    └─ rcheck | Component: ResPlaN | Calls: 259367 | Total: 187.0704s | Avg: 0.72ms | % of Parent: 8.1%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Total: 0.0000s | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-04-28 12:35:25*