# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 1
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Wall-Clock Time**: 2817.0287s (actual real time)
- **Total Profiled Time (Inclusive)**: 14949.3260s (sum of all sections)
- **Total Exclusive Time**: 2811.3397s (no nesting counted)
- **Unaccounted Time**: 5.6890s (0.2%)
- **Nesting Inflation Factor**: 5.32× (due to nested profiling sections)

*Note: Unaccounted time includes untracked code sections and profiling overhead.*

## Component Breakdown

| Component | Time (s) | Exclusive (s) | Calls | Avg Time (ms) | % of Exclusive |
|-----------|----------|---------------|-------|---------------|----------------|
| ResPlaN | 2958.3969 | 244.1413 | 769526 | 0.32 | 8.7% |
| CBS | 6774.3621 | 108.6071 | 857081 | 0.13 | 3.9% |
| SIPPS | 5216.5670 | 2458.5913 | 66842982 | 0.04 | 87.5% |

## Top 10 Time-Consuming Functions (Exclusive Time)

| Function | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of Total |
|----------|-------|----------------|----------------|---------------|------------|
| build_safe_interval_table | 337749 | 942.2450 | 942.2450 | 2.79 | 33.5% |
| SIPPS_node_creation | 13435158 | 700.3305 | 700.3305 | 0.05 | 24.9% |
| SIPPS_loop | 337749 | 1497.3488 | 329.9019 | 0.98 | 11.7% |
| SIPPS_goal_check | 2467659 | 258.0190 | 258.0190 | 0.10 | 9.2% |
| SIPPS_successor_processing | 14331330 | 874.0698 | 144.5709 | 0.01 | 5.1% |
| rcheck | 245707 | 142.0299 | 142.0299 | 0.58 | 5.1% |
| resplan_iteration | 250007 | 2813.5722 | 99.3166 | 0.40 | 3.5% |
| CBS_iteration | 143709 | 1702.3421 | 58.5519 | 0.41 | 2.1% |
| SIPPS_successor_generation | 2130444 | 27.9390 | 27.9390 | 0.01 | 1.0% |
| build_solution | 143709 | 19.5920 | 19.5920 | 0.14 | 0.7% |

## SIPPS Loop Operation Breakdown

| Operation | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of SIPPS |
|-----------|-------|----------------|----------------|---------------|-----------|
| SIPPS_node_creation | 13435158 | 700.3305 | 700.3305 | 0.05 | 46.8% |
| SIPPS_loop | 337749 | 1497.3488 | 329.9019 | 0.98 | 22.0% |
| SIPPS_goal_check | 2467659 | 258.0190 | 258.0190 | 0.10 | 17.2% |
| SIPPS_successor_processing | 14331330 | 874.0698 | 144.5709 | 0.01 | 9.7% |
| SIPPS_successor_generation | 2130444 | 27.9390 | 27.9390 | 0.01 | 1.9% |
| SIPPS_hard_constraint_check | 14331330 | 17.2383 | 17.2383 | 0.00 | 1.2% |
| SIPPS_soft_constraint_check | 13435158 | 11.9302 | 11.9302 | 0.00 | 0.8% |
| SIPPS_heap_pop | 2467659 | 5.5875 | 5.5875 | 0.00 | 0.4% |
| SIPPS_node_close | 2130444 | 1.8315 | 1.8315 | 0.00 | 0.1% |

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
ResPlaN | Component: ResPlaN | Total: 2817.0287s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 250007 | Total: 2813.5722s | Avg: 11.25ms | % of Parent: 99.9%
    └─ compute_plan_cbs | Component: CBS | Calls: 94820 | Total: 2567.2008s | Avg: 27.07ms | % of Parent: 91.2%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0043s | Avg: 4.30ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 87306 | Total: 862.6050s | Avg: 9.88ms | % of Parent: 33.6%
      └─ cbs_iteration | Component: CBS | Calls: 143709 | Total: 1702.3421s | Avg: 11.85ms | % of Parent: 66.3%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 143709 | Total: 19.5920s | Avg: 0.14ms | % of Parent: 1.2%
        └─ detect_conflict | Component: CBS | Calls: 137093 | Total: 13.3534s | Avg: 0.10ms | % of Parent: 0.8%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 250007 | Total: 0.3998s | Avg: 0.00ms | % of Parent: 0.0%
    └─ macroaction_loop | Component: ResPlaN | Calls: 23805 | Total: 2.3950s | Avg: 0.10ms | % of Parent: 0.1%
    └─ rcheck | Component: ResPlaN | Calls: 245707 | Total: 142.0299s | Avg: 0.58ms | % of Parent: 5.0%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Total: 0.0000s | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-05-01 12:02:32*