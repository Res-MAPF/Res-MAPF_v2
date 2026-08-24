# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 3
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Wall-Clock Time**: 3355.1928s (actual real time)
- **Total Profiled Time (Inclusive)**: 17414.1829s (sum of all sections)
- **Total Exclusive Time**: 3353.8972s (no nesting counted)
- **Unaccounted Time**: 1.2956s (0.0%)
- **Nesting Inflation Factor**: 5.19× (due to nested profiling sections)

*Note: Unaccounted time includes untracked code sections and profiling overhead.*

## Component Breakdown

| Component | Time (s) | Exclusive (s) | Calls | Avg Time (ms) | % of Exclusive |
|-----------|----------|---------------|-------|---------------|----------------|
| ResPlaN | 3396.0867 | 48.3144 | 157788 | 0.31 | 1.4% |
| CBS | 8039.5239 | 367.4642 | 259735 | 1.41 | 11.0% |
| SIPPS | 5978.5723 | 2938.1186 | 17631529 | 0.17 | 87.6% |

## Top 10 Time-Consuming Functions (Exclusive Time)

| Function | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of Total |
|----------|-------|----------------|----------------|---------------|------------|
| SIPPS_goal_check | 649188 | 1418.7482 | 1418.7482 | 2.19 | 42.3% |
| SIPPS_loop | 96063 | 2686.8792 | 1192.1011 | 12.41 | 35.5% |
| CBS_iteration | 49316 | 1789.3170 | 360.5632 | 7.31 | 10.8% |
| build_safe_interval_table | 96063 | 246.9207 | 246.9207 | 2.57 | 7.4% |
| rcheck | 49289 | 41.0712 | 41.0712 | 0.83 | 1.2% |
| SIPPS_successor_processing | 3666906 | 70.1750 | 39.8519 | 0.01 | 1.2% |
| SIPPS_node_creation | 3600600 | 22.6030 | 22.6030 | 0.01 | 0.7% |
| resplan_iteration | 51039 | 3354.3388 | 6.5665 | 0.13 | 0.2% |
| low_level_search_cbs | 96063 | 2942.7047 | 4.9744 | 0.05 | 0.1% |
| SIPPS_hard_constraint_check | 3666906 | 4.4235 | 4.4235 | 0.00 | 0.1% |

## SIPPS Loop Operation Breakdown

| Operation | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of SIPPS |
|-----------|-------|----------------|----------------|---------------|-----------|
| SIPPS_goal_check | 649188 | 1418.7482 | 1418.7482 | 2.19 | 52.8% |
| SIPPS_loop | 96063 | 2686.8792 | 1192.1011 | 12.41 | 44.4% |
| SIPPS_successor_processing | 3666906 | 70.1750 | 39.8519 | 0.01 | 1.5% |
| SIPPS_node_creation | 3600600 | 22.6030 | 22.6030 | 0.01 | 0.8% |
| SIPPS_hard_constraint_check | 3666906 | 4.4235 | 4.4235 | 0.00 | 0.2% |
| SIPPS_successor_generation | 553254 | 3.9150 | 3.9150 | 0.01 | 0.1% |
| SIPPS_soft_constraint_check | 3601013 | 3.2966 | 3.2966 | 0.00 | 0.1% |
| SIPPS_heap_pop | 649188 | 1.4537 | 1.4537 | 0.00 | 0.1% |
| SIPPS_node_close | 553254 | 0.4862 | 0.4862 | 0.00 | 0.0% |

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
ResPlaN | Component: ResPlaN | Total: 3355.1928s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 51039 | Total: 3354.3388s | Avg: 65.72ms | % of Parent: 100.0%
    └─ compute_plan_cbs | Component: CBS | Calls: 20525 | Total: 3305.5770s | Avg: 161.05ms | % of Parent: 98.5%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0057s | Avg: 5.70ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 18779 | Total: 1515.7407s | Avg: 80.71ms | % of Parent: 45.9%
      └─ cbs_iteration | Component: CBS | Calls: 49316 | Total: 1789.3170s | Avg: 36.28ms | % of Parent: 54.1%
        └─ cbs_vertex_conflict | Component: CBS | Calls: 42 | Total: 0.5023s | Avg: 11.96ms | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 49316 | Total: 0.8574s | Avg: 0.02ms | % of Parent: 0.0%
        └─ detect_conflict | Component: CBS | Calls: 44470 | Total: 0.5380s | Avg: 0.01ms | % of Parent: 0.0%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 51039 | Total: 0.0875s | Avg: 0.00ms | % of Parent: 0.0%
    └─ macroaction_loop | Component: ResPlaN | Calls: 6421 | Total: 0.5892s | Avg: 0.09ms | % of Parent: 0.0%
    └─ rcheck | Component: ResPlaN | Calls: 49289 | Total: 41.0712s | Avg: 0.83ms | % of Parent: 1.2%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Total: 0.0000s | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-05-01 10:52:01*