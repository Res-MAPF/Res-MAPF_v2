# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 2
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Wall-Clock Time**: 417.3703s (actual real time)
- **Total Profiled Time (Inclusive)**: 2049.9787s (sum of all sections)
- **Total Exclusive Time**: 415.3788s (no nesting counted)
- **Unaccounted Time**: 1.9915s (0.5%)
- **Nesting Inflation Factor**: 4.94× (due to nested profiling sections)

*Note: Unaccounted time includes untracked code sections and profiling overhead.*

## Component Breakdown

| Component | Time (s) | Exclusive (s) | Calls | Avg Time (ms) | % of Exclusive |
|-----------|----------|---------------|-------|---------------|----------------|
| ResPlaN | 451.7696 | 35.6200 | 163757 | 0.22 | 8.6% |
| CBS | 759.4856 | 3.9110 | 151908 | 0.03 | 0.9% |
| SIPPS | 838.7235 | 375.8478 | 6478128 | 0.06 | 90.5% |

## Top 10 Time-Consuming Functions (Exclusive Time)

| Function | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of Total |
|----------|-------|----------------|----------------|---------------|------------|
| build_safe_interval_table | 65103 | 290.8690 | 290.8690 | 4.47 | 70.0% |
| SIPPS_goal_check | 250897 | 50.3501 | 50.3501 | 0.20 | 12.1% |
| rcheck | 51899 | 34.8448 | 34.8448 | 0.67 | 8.4% |
| SIPPS_successor_processing | 1281831 | 22.8016 | 13.1234 | 0.01 | 3.2% |
| SIPPS_loop | 65103 | 82.3508 | 7.3323 | 0.11 | 1.8% |
| SIPPS_node_creation | 1281831 | 7.1410 | 7.1410 | 0.01 | 1.7% |
| low_level_search_cbs | 65103 | 378.1790 | 2.7123 | 0.04 | 0.7% |
| SIPPS_hard_constraint_check | 1281831 | 1.4414 | 1.4414 | 0.00 | 0.3% |
| SIPPS_successor_generation | 185794 | 1.2565 | 1.2565 | 0.01 | 0.3% |
| SIPPS_soft_constraint_check | 1281831 | 1.0959 | 1.0959 | 0.00 | 0.3% |

## SIPPS Loop Operation Breakdown

| Operation | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of SIPPS |
|-----------|-------|----------------|----------------|---------------|-----------|
| SIPPS_goal_check | 250897 | 50.3501 | 50.3501 | 0.20 | 61.1% |
| SIPPS_successor_processing | 1281831 | 22.8016 | 13.1234 | 0.01 | 15.9% |
| SIPPS_loop | 65103 | 82.3508 | 7.3323 | 0.11 | 8.9% |
| SIPPS_node_creation | 1281831 | 7.1410 | 7.1410 | 0.01 | 8.7% |
| SIPPS_hard_constraint_check | 1281831 | 1.4414 | 1.4414 | 0.00 | 1.8% |
| SIPPS_successor_generation | 185794 | 1.2565 | 1.2565 | 0.01 | 1.5% |
| SIPPS_soft_constraint_check | 1281831 | 1.0959 | 1.0959 | 0.00 | 1.3% |
| SIPPS_heap_pop | 250897 | 0.4610 | 0.4610 | 0.00 | 0.6% |
| SIPPS_node_close | 185794 | 0.1492 | 0.1492 | 0.00 | 0.2% |

## Performance Notes

**Time Attribution**:

- **Inclusive Time**: Total time a section ran (including time in nested children)
- **Exclusive Time**: Time spent directly in that section (excluding children)
- **Unaccounted**: Wall-clock - Exclusive = overhead and untracked code

**Constraint Checking Costs** (if available):

**Note on `low_level_search_cbs`**: This function is called from multiple contexts:
- During root CBS initialization (~15-20% of calls)
- During CBS conflict resolution iterations (~80-85% of calls)
The time reported includes ALL calls aggregated across both contexts.

## Detailed Granular Statistics

<pre style="overflow-x: auto; white-space: pre;">
ResPlaN | Component: ResPlaN | Total: 417.3703s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 53034 | Total: 416.3039s | Avg: 7.85ms | % of Parent: 99.7%
    └─ compute_plan_cbs | Component: CBS | Calls: 21701 | Total: 379.7529s | Avg: 17.50ms | % of Parent: 91.2%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0061s | Avg: 6.10ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 21701 | Total: 378.5602s | Avg: 17.44ms | % of Parent: 99.7%
      └─ cbs_iteration | Component: CBS | Calls: 21701 | Total: 0.9042s | Avg: 0.04ms | % of Parent: 0.2%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 21701 | Total: 0.3820s | Avg: 0.02ms | % of Parent: 42.2%
        └─ detect_conflict | Component: CBS | Calls: 21701 | Total: 0.2614s | Avg: 0.01ms | % of Parent: 28.9%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 53034 | Total: 0.0773s | Avg: 0.00ms | % of Parent: 0.0%
    └─ macroaction_loop | Component: ResPlaN | Calls: 5789 | Total: 0.4932s | Avg: 0.09ms | % of Parent: 0.1%
    └─ rcheck | Component: ResPlaN | Calls: 51899 | Total: 34.8448s | Avg: 0.67ms | % of Parent: 8.4%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.0504s | Avg: 50.40ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-05-01 09:56:04*