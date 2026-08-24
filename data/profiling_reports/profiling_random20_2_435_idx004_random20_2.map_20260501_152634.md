# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 4
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Wall-Clock Time**: 426.2867s (actual real time)
- **Total Profiled Time (Inclusive)**: 2001.5490s (sum of all sections)
- **Total Exclusive Time**: 423.0283s (no nesting counted)
- **Unaccounted Time**: 3.2584s (0.8%)
- **Nesting Inflation Factor**: 4.73× (due to nested profiling sections)

*Note: Unaccounted time includes untracked code sections and profiling overhead.*

## Component Breakdown

| Component | Time (s) | Exclusive (s) | Calls | Avg Time (ms) | % of Exclusive |
|-----------|----------|---------------|-------|---------------|----------------|
| ResPlaN | 497.9802 | 74.5685 | 232227 | 0.32 | 17.6% |
| CBS | 696.7597 | 5.7644 | 200572 | 0.03 | 1.4% |
| SIPPS | 806.8091 | 342.6954 | 8441089 | 0.04 | 81.0% |

## Top 10 Time-Consuming Functions (Exclusive Time)

| Function | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of Total |
|----------|-------|----------------|----------------|---------------|------------|
| build_safe_interval_table | 85959 | 222.7776 | 222.7776 | 2.59 | 52.7% |
| SIPPS_goal_check | 324790 | 73.4378 | 73.4378 | 0.23 | 17.4% |
| rcheck | 73729 | 72.6103 | 72.6103 | 0.98 | 17.2% |
| SIPPS_successor_processing | 1692360 | 30.6092 | 19.2484 | 0.01 | 4.6% |
| SIPPS_loop | 85959 | 117.5902 | 10.8117 | 0.13 | 2.6% |
| SIPPS_node_creation | 1692360 | 7.6656 | 7.6656 | 0.00 | 1.8% |
| low_level_search_cbs | 85959 | 345.9745 | 3.9000 | 0.05 | 0.9% |
| SIPPS_hard_constraint_check | 1692360 | 2.1037 | 2.1037 | 0.00 | 0.5% |
| SIPPS_successor_generation | 238831 | 1.8473 | 1.8473 | 0.01 | 0.4% |
| SIPPS_soft_constraint_check | 1692360 | 1.5914 | 1.5914 | 0.00 | 0.4% |

## SIPPS Loop Operation Breakdown

| Operation | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of SIPPS |
|-----------|-------|----------------|----------------|---------------|-----------|
| SIPPS_goal_check | 324790 | 73.4378 | 73.4378 | 0.23 | 62.5% |
| SIPPS_successor_processing | 1692360 | 30.6092 | 19.2484 | 0.01 | 16.4% |
| SIPPS_loop | 85959 | 117.5902 | 10.8117 | 0.13 | 9.2% |
| SIPPS_node_creation | 1692360 | 7.6656 | 7.6656 | 0.00 | 6.5% |
| SIPPS_hard_constraint_check | 1692360 | 2.1037 | 2.1037 | 0.00 | 1.8% |
| SIPPS_successor_generation | 238831 | 1.8473 | 1.8473 | 0.01 | 1.6% |
| SIPPS_soft_constraint_check | 1692360 | 1.5914 | 1.5914 | 0.00 | 1.4% |
| SIPPS_heap_pop | 324790 | 0.6725 | 0.6725 | 0.00 | 0.6% |
| SIPPS_node_close | 238831 | 0.2118 | 0.2118 | 0.00 | 0.2% |

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
ResPlaN | Component: ResPlaN | Total: 426.2867s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 74950 | Total: 424.2005s | Avg: 5.66ms | % of Parent: 99.5%
    └─ compute_plan_cbs | Component: CBS | Calls: 28653 | Total: 348.4546s | Avg: 12.16ms | % of Parent: 82.1%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0052s | Avg: 5.20ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 28653 | Total: 346.5953s | Avg: 12.10ms | % of Parent: 99.5%
      └─ cbs_iteration | Component: CBS | Calls: 28653 | Total: 1.3765s | Avg: 0.05ms | % of Parent: 0.4%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 28653 | Total: 0.5642s | Avg: 0.02ms | % of Parent: 41.0%
        └─ detect_conflict | Component: CBS | Calls: 28653 | Total: 0.3847s | Avg: 0.01ms | % of Parent: 27.9%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 74950 | Total: 0.1357s | Avg: 0.00ms | % of Parent: 0.0%
    └─ macroaction_loop | Component: ResPlaN | Calls: 8597 | Total: 0.9683s | Avg: 0.11ms | % of Parent: 0.2%
    └─ rcheck | Component: ResPlaN | Calls: 73729 | Total: 72.6103s | Avg: 0.98ms | % of Parent: 17.1%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.0654s | Avg: 65.40ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-05-01 15:26:34*