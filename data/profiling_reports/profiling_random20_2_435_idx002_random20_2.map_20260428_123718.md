# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 2
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Time**: 112.4308s (actual wall-clock execution time)
- **Time from Analysis**: 458.8161s (sum of all profiled sections)

*Note: These times may differ due to profiling overhead and untracked code sections.*

## Component Breakdown

| Component | Time (s) | Calls | Avg Time (ms) | % of Total |
|-----------|----------|-------|---------------|------------|
| ResPlaN | 141.3943 | 173613 | 0.81 | 30.8% |
| CBS | 157.3690 | 156703 | 1.00 | 34.3% |
| SIPPS | 160.0732 | 4736991 | 0.03 | 34.9% |

## Top 5 Time-Consuming Functions

| Function | Calls | Total Time (s) | Avg Time (ms) |
|----------|-------|----------------|---------------|
| resplan_iteration | 56163 | 110.4869 | 1.97 |
| compute_plan_cbs | 22386 | 78.6741 | 3.51 |
| root_compute_low_level_solution | 22386 | 77.5275 | 3.46 |
| low_level_search_cbs | 67158 | 77.1748 | 1.15 |
| SIPPS_loop | 67158 | 68.8439 | 1.03 |

## Performance Notes

**Note on `low_level_search_cbs`**: This function is called from multiple contexts:
- During root CBS initialization (~15-20% of calls)
- During CBS conflict resolution iterations (~80-85% of calls)
The time reported includes ALL calls aggregated across both contexts.

## Detailed Granular Statistics

<pre style="overflow-x: auto; white-space: pre;">
ResPlaN | Component: ResPlaN | Total: 112.4308s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 56163 | Total: 110.4869s | Avg: 1.97ms | % of Parent: 98.3%
    └─ compute_plan_cbs | Component: CBS | Calls: 22386 | Total: 78.6741s | Avg: 3.51ms | % of Parent: 71.2%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0051s | Avg: 5.10ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 22386 | Total: 77.5275s | Avg: 3.46ms | % of Parent: 98.5%
      └─ cbs_iteration | Component: CBS | Calls: 22386 | Total: 0.8768s | Avg: 0.04ms | % of Parent: 1.1%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 22386 | Total: 0.3727s | Avg: 0.02ms | % of Parent: 42.5%
        └─ detect_conflict | Component: CBS | Calls: 22386 | Total: 0.2655s | Avg: 0.01ms | % of Parent: 30.3%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 56163 | Total: 0.0745s | Avg: 0.00ms | % of Parent: 0.1%
    └─ macroaction_loop | Component: ResPlaN | Calls: 6266 | Total: 0.5256s | Avg: 0.08ms | % of Parent: 0.5%
    └─ rcheck | Component: ResPlaN | Calls: 55020 | Total: 30.2590s | Avg: 0.55ms | % of Parent: 27.4%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.0483s | Avg: 48.30ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-04-28 12:37:18*