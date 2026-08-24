# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 1
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Wall-Clock Time**: 1149.2505s (actual real time)
- **Total Profiled Time (Inclusive)**: 5584.2231s (sum of all sections)
- **Total Exclusive Time**: 1141.5075s (no nesting counted)
- **Unaccounted Time**: 7.7430s (0.7%)
- **Nesting Inflation Factor**: 4.89× (due to nested profiling sections)

*Note: Unaccounted time includes untracked code sections and profiling overhead.*

## Component Breakdown

| Component | Time (s) | Exclusive (s) | Calls | Avg Time (ms) | % of Exclusive |
|-----------|----------|---------------|-------|---------------|----------------|
| ResPlaN | 1306.0767 | 162.5410 | 691113 | 0.24 | 14.2% |
| CBS | 1957.7007 | 16.5243 | 523944 | 0.03 | 1.4% |
| SIPPS | 2320.4457 | 962.4422 | 27063208 | 0.04 | 84.3% |

## Top 10 Time-Consuming Functions (Exclusive Time)

| Function | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of Total |
|----------|-------|----------------|----------------|---------------|------------|
| build_safe_interval_table | 224547 | 578.5170 | 578.5170 | 2.58 | 50.7% |
| SIPPS_goal_check | 1058720 | 210.9042 | 210.9042 | 0.20 | 18.5% |
| rcheck | 222951 | 158.2022 | 158.2022 | 0.71 | 13.9% |
| SIPPS_successor_processing | 5407686 | 115.7049 | 65.7969 | 0.01 | 5.8% |
| SIPPS_loop | 224547 | 373.0650 | 37.2388 | 0.17 | 3.3% |
| SIPPS_node_creation | 5407686 | 36.9997 | 36.9997 | 0.01 | 3.2% |
| low_level_search_cbs | 224547 | 972.2693 | 11.4903 | 0.05 | 1.0% |
| SIPPS_hard_constraint_check | 5407686 | 7.3605 | 7.3605 | 0.00 | 0.6% |
| SIPPS_successor_generation | 834173 | 6.0454 | 6.0454 | 0.01 | 0.5% |
| SIPPS_soft_constraint_check | 5407686 | 5.5478 | 5.5478 | 0.00 | 0.5% |

## SIPPS Loop Operation Breakdown

| Operation | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of SIPPS |
|-----------|-------|----------------|----------------|---------------|-----------|
| SIPPS_goal_check | 1058720 | 210.9042 | 210.9042 | 0.20 | 56.5% |
| SIPPS_successor_processing | 5407686 | 115.7049 | 65.7969 | 0.01 | 17.6% |
| SIPPS_loop | 224547 | 373.0650 | 37.2388 | 0.17 | 10.0% |
| SIPPS_node_creation | 5407686 | 36.9997 | 36.9997 | 0.01 | 9.9% |
| SIPPS_hard_constraint_check | 5407686 | 7.3605 | 7.3605 | 0.00 | 2.0% |
| SIPPS_successor_generation | 834173 | 6.0454 | 6.0454 | 0.01 | 1.6% |
| SIPPS_soft_constraint_check | 5407686 | 5.5478 | 5.5478 | 0.00 | 1.5% |
| SIPPS_heap_pop | 1058720 | 2.3635 | 2.3635 | 0.00 | 0.6% |
| SIPPS_node_close | 834173 | 0.8083 | 0.8083 | 0.00 | 0.2% |

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
ResPlaN | Component: ResPlaN | Total: 1149.2505s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 224868 | Total: 1145.0985s | Avg: 5.09ms | % of Parent: 99.6%
    └─ compute_plan_cbs | Component: CBS | Calls: 74849 | Total: 978.9506s | Avg: 13.08ms | % of Parent: 85.5%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0157s | Avg: 15.70ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 74849 | Total: 973.9323s | Avg: 13.01ms | % of Parent: 99.5%
      └─ cbs_iteration | Component: CBS | Calls: 74849 | Total: 3.7852s | Avg: 0.05ms | % of Parent: 0.4%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 74849 | Total: 1.5660s | Avg: 0.02ms | % of Parent: 41.4%
        └─ detect_conflict | Component: CBS | Calls: 74849 | Total: 1.1139s | Avg: 0.01ms | % of Parent: 29.4%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 224868 | Total: 0.3880s | Avg: 0.00ms | % of Parent: 0.0%
    └─ macroaction_loop | Component: ResPlaN | Calls: 18425 | Total: 2.2149s | Avg: 0.12ms | % of Parent: 0.2%
    └─ rcheck | Component: ResPlaN | Calls: 222951 | Total: 158.2022s | Avg: 0.71ms | % of Parent: 13.8%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.1731s | Avg: 173.10ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-05-01 09:49:02*