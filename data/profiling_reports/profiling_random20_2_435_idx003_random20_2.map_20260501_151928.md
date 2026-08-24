# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 3
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Wall-Clock Time**: 10414.0993s (actual real time)
- **Total Profiled Time (Inclusive)**: 52066.3633s (sum of all sections)
- **Total Exclusive Time**: 10411.7667s (no nesting counted)
- **Unaccounted Time**: 2.3326s (0.0%)
- **Nesting Inflation Factor**: 5.00× (due to nested profiling sections)

*Note: Unaccounted time includes untracked code sections and profiling overhead.*

## Component Breakdown

| Component | Time (s) | Exclusive (s) | Calls | Avg Time (ms) | % of Exclusive |
|-----------|----------|---------------|-------|---------------|----------------|
| ResPlaN | 10465.8480 | 61.9307 | 157582 | 0.39 | 0.6% |
| CBS | 22335.7303 | 11.5301 | 258594 | 0.04 | 0.1% |
| SIPPS | 19264.7850 | 10338.3059 | 17480342 | 0.59 | 99.3% |

## Top 10 Time-Consuming Functions (Exclusive Time)

| Function | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of Total |
|----------|-------|----------------|----------------|---------------|------------|
| build_safe_interval_table | 95622 | 10120.7017 | 10120.7017 | 105.84 | 97.2% |
| SIPPS_goal_check | 647146 | 98.5101 | 98.5101 | 0.15 | 0.9% |
| rcheck | 49222 | 52.7656 | 52.7656 | 1.07 | 0.5% |
| SIPPS_successor_processing | 3655405 | 80.8072 | 49.9717 | 0.01 | 0.5% |
| SIPPS_loop | 95622 | 214.6323 | 27.8620 | 0.29 | 0.3% |
| SIPPS_node_creation | 3589525 | 21.1240 | 21.1240 | 0.01 | 0.2% |
| resplan_iteration | 50971 | 10412.2304 | 8.3131 | 0.16 | 0.1% |
| low_level_search_cbs | 95622 | 10343.6819 | 5.9276 | 0.06 | 0.1% |
| SIPPS_hard_constraint_check | 3655405 | 5.6063 | 5.6063 | 0.00 | 0.1% |
| SIPPS_successor_generation | 551654 | 5.0288 | 5.0288 | 0.01 | 0.0% |

## SIPPS Loop Operation Breakdown

| Operation | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of SIPPS |
|-----------|-------|----------------|----------------|---------------|-----------|
| SIPPS_goal_check | 647146 | 98.5101 | 98.5101 | 0.15 | 45.9% |
| SIPPS_successor_processing | 3655405 | 80.8072 | 49.9717 | 0.01 | 23.3% |
| SIPPS_loop | 95622 | 214.6323 | 27.8620 | 0.29 | 13.0% |
| SIPPS_node_creation | 3589525 | 21.1240 | 21.1240 | 0.01 | 9.8% |
| SIPPS_hard_constraint_check | 3655405 | 5.6063 | 5.6063 | 0.00 | 2.6% |
| SIPPS_successor_generation | 551654 | 5.0288 | 5.0288 | 0.01 | 2.3% |
| SIPPS_soft_constraint_check | 3589935 | 4.1052 | 4.1052 | 0.00 | 1.9% |
| SIPPS_heap_pop | 647146 | 1.8152 | 1.8152 | 0.00 | 0.8% |
| SIPPS_node_close | 551654 | 0.6090 | 0.6090 | 0.00 | 0.3% |

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
ResPlaN | Component: ResPlaN | Total: 10414.0993s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 50971 | Total: 10412.2304s | Avg: 204.28ms | % of Parent: 100.0%
    └─ compute_plan_cbs | Component: CBS | Calls: 20494 | Total: 10349.8292s | Avg: 505.02ms | % of Parent: 99.4%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0069s | Avg: 6.90ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 18740 | Total: 8709.4250s | Avg: 464.75ms | % of Parent: 84.2%
      └─ cbs_iteration | Component: CBS | Calls: 49083 | Total: 1639.6877s | Avg: 33.41ms | % of Parent: 15.8%
        └─ cbs_vertex_conflict | Component: CBS | Calls: 42 | Total: 0.7192s | Avg: 17.12ms | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 49083 | Total: 1.0977s | Avg: 0.02ms | % of Parent: 0.1%
        └─ detect_conflict | Component: CBS | Calls: 44267 | Total: 0.6811s | Avg: 0.02ms | % of Parent: 0.0%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 50971 | Total: 0.1285s | Avg: 0.00ms | % of Parent: 0.0%
    └─ macroaction_loop | Component: ResPlaN | Calls: 6418 | Total: 0.7235s | Avg: 0.11ms | % of Parent: 0.0%
    └─ rcheck | Component: ResPlaN | Calls: 49222 | Total: 52.7656s | Avg: 1.07ms | % of Parent: 0.5%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Total: 0.0000s | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-05-01 15:19:28*