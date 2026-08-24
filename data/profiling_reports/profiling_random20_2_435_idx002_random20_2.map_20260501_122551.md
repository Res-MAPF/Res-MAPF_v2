# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 2
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Wall-Clock Time**: 405.6973s (actual real time)
- **Total Profiled Time (Inclusive)**: 1973.3453s (sum of all sections)
- **Total Exclusive Time**: 402.0233s (no nesting counted)
- **Unaccounted Time**: 3.6740s (0.9%)
- **Nesting Inflation Factor**: 4.91× (due to nested profiling sections)

*Note: Unaccounted time includes untracked code sections and profiling overhead.*

## Component Breakdown

| Component | Time (s) | Exclusive (s) | Calls | Avg Time (ms) | % of Exclusive |
|-----------|----------|---------------|-------|---------------|----------------|
| ResPlaN | 451.3137 | 50.1589 | 173613 | 0.29 | 12.5% |
| CBS | 703.5115 | 6.6732 | 156703 | 0.04 | 1.7% |
| SIPPS | 818.5201 | 345.1912 | 6667934 | 0.05 | 85.9% |

## Top 10 Time-Consuming Functions (Exclusive Time)

| Function | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of Total |
|----------|-------|----------------|----------------|---------------|------------|
| build_safe_interval_table | 67158 | 218.9239 | 218.9239 | 3.26 | 54.5% |
| SIPPS_goal_check | 269282 | 75.4187 | 75.4187 | 0.28 | 18.8% |
| rcheck | 55020 | 47.5706 | 47.5706 | 0.86 | 11.8% |
| SIPPS_successor_processing | 1324947 | 33.0212 | 20.4976 | 0.02 | 5.1% |
| SIPPS_loop | 67158 | 123.6978 | 11.9642 | 0.18 | 3.0% |
| SIPPS_node_creation | 1324947 | 8.5781 | 8.5781 | 0.01 | 2.1% |
| low_level_search_cbs | 67158 | 349.0717 | 4.5916 | 0.07 | 1.1% |
| SIPPS_hard_constraint_check | 1324947 | 2.2467 | 2.2467 | 0.00 | 0.6% |
| SIPPS_successor_generation | 202124 | 2.2347 | 2.2347 | 0.01 | 0.6% |
| SIPPS_soft_constraint_check | 1324947 | 1.6987 | 1.6987 | 0.00 | 0.4% |

## SIPPS Loop Operation Breakdown

| Operation | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of SIPPS |
|-----------|-------|----------------|----------------|---------------|-----------|
| SIPPS_goal_check | 269282 | 75.4187 | 75.4187 | 0.28 | 61.0% |
| SIPPS_successor_processing | 1324947 | 33.0212 | 20.4976 | 0.02 | 16.6% |
| SIPPS_loop | 67158 | 123.6978 | 11.9642 | 0.18 | 9.7% |
| SIPPS_node_creation | 1324947 | 8.5781 | 8.5781 | 0.01 | 6.9% |
| SIPPS_hard_constraint_check | 1324947 | 2.2467 | 2.2467 | 0.00 | 1.8% |
| SIPPS_successor_generation | 202124 | 2.2347 | 2.2347 | 0.01 | 1.8% |
| SIPPS_soft_constraint_check | 1324947 | 1.6987 | 1.6987 | 0.00 | 1.4% |
| SIPPS_heap_pop | 269282 | 0.7748 | 0.7748 | 0.00 | 0.6% |
| SIPPS_node_close | 202124 | 0.2842 | 0.2842 | 0.00 | 0.2% |

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
ResPlaN | Component: ResPlaN | Total: 405.6973s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 56163 | Total: 402.5783s | Avg: 7.17ms | % of Parent: 99.2%
    └─ compute_plan_cbs | Component: CBS | Calls: 22386 | Total: 351.8607s | Avg: 15.72ms | % of Parent: 87.4%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0039s | Avg: 3.90ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 22386 | Total: 349.7829s | Avg: 15.63ms | % of Parent: 99.4%
      └─ cbs_iteration | Component: CBS | Calls: 22386 | Total: 1.5270s | Avg: 0.07ms | % of Parent: 0.4%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 22386 | Total: 0.6328s | Avg: 0.03ms | % of Parent: 41.4%
        └─ detect_conflict | Component: CBS | Calls: 22386 | Total: 0.4154s | Avg: 0.02ms | % of Parent: 27.2%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 56163 | Total: 0.1372s | Avg: 0.00ms | % of Parent: 0.0%
    └─ macroaction_loop | Component: ResPlaN | Calls: 6266 | Total: 0.9259s | Avg: 0.15ms | % of Parent: 0.2%
    └─ rcheck | Component: ResPlaN | Calls: 55020 | Total: 47.5706s | Avg: 0.86ms | % of Parent: 11.8%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.1017s | Avg: 101.70ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-05-01 12:25:51*