# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 4
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Time**: 171.6303s (actual wall-clock execution time)
- **Time from Analysis**: 659.2857s (sum of all profiled sections)

*Note: These times may differ due to profiling overhead and untracked code sections.*

## Component Breakdown

| Component | Time (s) | Calls | Avg Time (ms) | % of Total |
|-----------|----------|-------|---------------|------------|
| ResPlaN | 233.2304 | 232227 | 1.00 | 35.4% |
| CBS | 211.2127 | 200572 | 1.05 | 32.0% |
| SIPPS | 214.7397 | 6032180 | 0.04 | 32.6% |

## Top 5 Time-Consuming Functions

| Function | Calls | Total Time (s) | Avg Time (ms) |
|----------|-------|----------------|---------------|
| resplan_iteration | 74950 | 170.0004 | 2.27 |
| compute_plan_cbs | 28653 | 105.6118 | 3.69 |
| root_compute_low_level_solution | 28653 | 104.0892 | 3.63 |
| low_level_search_cbs | 85959 | 103.6123 | 1.21 |
| SIPPS_loop | 85959 | 92.5387 | 1.08 |

## Performance Notes

**Note on `low_level_search_cbs`**: This function is called from multiple contexts:
- During root CBS initialization (~15-20% of calls)
- During CBS conflict resolution iterations (~80-85% of calls)
The time reported includes ALL calls aggregated across both contexts.

## Detailed Granular Statistics

<pre style="overflow-x: auto; white-space: pre;">
ResPlaN | Component: ResPlaN | Total: 171.6303s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 74950 | Total: 170.0004s | Avg: 2.27ms | % of Parent: 99.1%
    └─ compute_plan_cbs | Component: CBS | Calls: 28653 | Total: 105.6118s | Avg: 3.69ms | % of Parent: 62.1%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0053s | Avg: 5.30ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 28653 | Total: 104.0892s | Avg: 3.63ms | % of Parent: 98.6%
      └─ cbs_iteration | Component: CBS | Calls: 28653 | Total: 1.1511s | Avg: 0.04ms | % of Parent: 1.1%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 28653 | Total: 0.4853s | Avg: 0.02ms | % of Parent: 42.2%
        └─ detect_conflict | Component: CBS | Calls: 28653 | Total: 0.3469s | Avg: 0.01ms | % of Parent: 30.1%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 74950 | Total: 0.1073s | Avg: 0.00ms | % of Parent: 0.1%
    └─ macroaction_loop | Component: ResPlaN | Calls: 8597 | Total: 0.7189s | Avg: 0.08ms | % of Parent: 0.4%
    └─ rcheck | Component: ResPlaN | Calls: 73729 | Total: 62.3410s | Avg: 0.85ms | % of Parent: 36.7%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.0628s | Avg: 62.80ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-04-28 12:45:58*