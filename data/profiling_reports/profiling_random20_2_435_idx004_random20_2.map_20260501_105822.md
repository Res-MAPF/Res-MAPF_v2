# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 4
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Wall-Clock Time**: 380.5713s (actual real time)
- **Total Profiled Time (Inclusive)**: 1812.1259s (sum of all sections)
- **Total Exclusive Time**: 377.8477s (no nesting counted)
- **Unaccounted Time**: 2.7236s (0.7%)
- **Nesting Inflation Factor**: 4.80× (due to nested profiling sections)

*Note: Unaccounted time includes untracked code sections and profiling overhead.*

## Component Breakdown

| Component | Time (s) | Exclusive (s) | Calls | Avg Time (ms) | % of Exclusive |
|-----------|----------|---------------|-------|---------------|----------------|
| ResPlaN | 439.7705 | 60.8903 | 232227 | 0.26 | 16.1% |
| CBS | 633.7995 | 5.4350 | 200572 | 0.03 | 1.4% |
| SIPPS | 738.5559 | 311.5224 | 8526472 | 0.04 | 82.4% |

## Top 10 Time-Consuming Functions (Exclusive Time)

| Function | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of Total |
|----------|-------|----------------|----------------|---------------|------------|
| build_safe_interval_table | 85959 | 198.9077 | 198.9077 | 2.31 | 52.6% |
| SIPPS_goal_check | 324766 | 66.8338 | 66.8338 | 0.21 | 17.7% |
| rcheck | 73729 | 59.7458 | 59.7458 | 0.81 | 15.8% |
| SIPPS_successor_processing | 1692240 | 30.0997 | 17.2652 | 0.01 | 4.6% |
| SIPPS_loop | 85959 | 109.0071 | 9.6325 | 0.11 | 2.5% |
| SIPPS_node_creation | 1692240 | 9.4747 | 9.4747 | 0.01 | 2.5% |
| low_level_search_cbs | 85959 | 314.8243 | 3.8369 | 0.04 | 1.0% |
| SIPPS_hard_constraint_check | 1692240 | 1.9117 | 1.9117 | 0.00 | 0.5% |
| SIPPS_successor_generation | 238807 | 1.6500 | 1.6500 | 0.01 | 0.4% |
| SIPPS_soft_constraint_check | 1692240 | 1.4480 | 1.4480 | 0.00 | 0.4% |

## SIPPS Loop Operation Breakdown

| Operation | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of SIPPS |
|-----------|-------|----------------|----------------|---------------|-----------|
| SIPPS_goal_check | 324766 | 66.8338 | 66.8338 | 0.21 | 61.3% |
| SIPPS_successor_processing | 1692240 | 30.0997 | 17.2652 | 0.01 | 15.8% |
| SIPPS_loop | 85959 | 109.0071 | 9.6325 | 0.11 | 8.8% |
| SIPPS_node_creation | 1692240 | 9.4747 | 9.4747 | 0.01 | 8.7% |
| SIPPS_hard_constraint_check | 1692240 | 1.9117 | 1.9117 | 0.00 | 1.8% |
| SIPPS_successor_generation | 238807 | 1.6500 | 1.6500 | 0.01 | 1.5% |
| SIPPS_soft_constraint_check | 1692240 | 1.4480 | 1.4480 | 0.00 | 1.3% |
| SIPPS_heap_pop | 324766 | 0.5991 | 0.5991 | 0.00 | 0.5% |
| SIPPS_node_close | 238807 | 0.1921 | 0.1921 | 0.00 | 0.2% |

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
ResPlaN | Component: ResPlaN | Total: 380.5713s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 74950 | Total: 379.1133s | Avg: 5.06ms | % of Parent: 99.6%
    └─ compute_plan_cbs | Component: CBS | Calls: 28653 | Total: 316.9521s | Avg: 11.06ms | % of Parent: 83.6%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0052s | Avg: 5.20ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 28653 | Total: 315.3593s | Avg: 11.01ms | % of Parent: 99.5%
      └─ cbs_iteration | Component: CBS | Calls: 28653 | Total: 1.1873s | Avg: 0.04ms | % of Parent: 0.4%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 28653 | Total: 0.4889s | Avg: 0.02ms | % of Parent: 41.2%
        └─ detect_conflict | Component: CBS | Calls: 28653 | Total: 0.3417s | Avg: 0.01ms | % of Parent: 28.8%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 74950 | Total: 0.1139s | Avg: 0.00ms | % of Parent: 0.0%
    └─ macroaction_loop | Component: ResPlaN | Calls: 8597 | Total: 0.7318s | Avg: 0.09ms | % of Parent: 0.2%
    └─ rcheck | Component: ResPlaN | Calls: 73729 | Total: 59.7458s | Avg: 0.81ms | % of Parent: 15.8%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.0657s | Avg: 65.70ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-05-01 10:58:22*