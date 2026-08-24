# Profiling Report - ResPlaN MAPF

## Instance Information

- **Test Set**: random20_2_435
- **Instance Index**: 1
- **Map**: random20_2.map
- **Agents**: 3
- **Parameters**: k=3, m=3, h=2
- **Failure Types**: topw, individual

## Execution Summary

- **Total Time**: 1216.1497s (actual wall-clock execution time)
- **Time from Analysis**: 5019.9257s (sum of all profiled sections)

*Note: These times may differ due to profiling overhead and untracked code sections.*

## Component Breakdown

| Component | Time (s) | Calls | Avg Time (ms) | % of Total |
|-----------|----------|-------|---------------|------------|
| ResPlaN | 1554.9588 | 691113 | 2.25 | 31.0% |
| CBS | 1701.3288 | 523944 | 3.25 | 33.9% |
| SIPPS | 1763.6319 | 18928456 | 0.09 | 35.1% |

## Top 5 Time-Consuming Functions

| Function | Calls | Total Time (s) | Avg Time (ms) |
|----------|-------|----------------|---------------|
| resplan_iteration | 224868 | 1208.1081 | 5.37 |
| compute_plan_cbs | 74849 | 850.9466 | 11.37 |
| root_compute_low_level_solution | 74849 | 839.8851 | 11.22 |
| low_level_search_cbs | 224547 | 836.1158 | 3.72 |
| SIPPS_loop | 224547 | 739.6115 | 3.29 |

## Detailed Granular Statistics

<pre style="overflow-x: auto; white-space: pre;">
ResPlaN | Component: ResPlaN | Total: 1216.1497s | % of Total: 100.0%
  └─ resplan_iteration | Component: ResPlaN | Calls: 224868 | Total: 1208.1081s | Avg: 5.37ms | % of Parent: 99.3%
    └─ compute_plan_cbs | Component: CBS | Calls: 74849 | Total: 850.9466s | Avg: 11.37ms | % of Parent: 70.4%
      └─ heuristic_computation | Component: CBS | Calls: 1 | Total: 0.0095s | Avg: 9.50ms | % of Parent: 0.0%
      └─ root_compute_low_level_solution | Component: SIPPS | Calls: 74849 | Total: 839.8851s | Avg: 11.22ms | % of Parent: 98.7%
        └─ low_level_search_cbs | Component: CBS | Calls: 224547 | Total: 836.1158s | Avg: 3.72ms | % of Parent: 99.6%
          └─ populate_hard_constraints | Component: SIPPS | Calls: 224547 | Total: 0.5333s | Avg: 0.00ms | % of Parent: 0.1%
          └─ populate_soft_constraints | Component: SIPPS | Calls: 224547 | Total: 3.4298s | Avg: 0.02ms | % of Parent: 0.4%
          └─ area_capacity_soft_constraints | Component: SIPPS | Calls: 224547 | Total: 0.9107s | Avg: 0.00ms | % of Parent: 0.1%
          └─ graph_modification | Component: SIPPS | Calls: 224547 | Total: 2.5914s | Avg: 0.01ms | % of Parent: 0.3%
          └─ build_safe_interval_table | Component: SIPPS | Calls: 224547 | Total: 58.4305s | Avg: 0.26ms | % of Parent: 7.0%
          └─ compute_goal_times | Component: SIPPS | Calls: 224547 | Total: 6.7344s | Avg: 0.03ms | % of Parent: 0.8%
          └─ create_root_sipps_node | Component: SIPPS | Total: 0.0000s | % of Parent: 0.0%
          └─ sipps_loop | Component: SIPPS | Calls: 224547 | Total: 739.6115s | Avg: 3.29ms | % of Parent: 88.5%
            └─ SIPPS_node_expansion | Component: SIPPS | Calls: 1058720 | Total: 5.2074s | Avg: 0.00ms | % of Parent: 0.7%
            └─ hard_constraint_check | Component: SIPPS | Calls: 5407686 | Total: 16.3950s | Avg: 0.00ms | % of Parent: 2.2%
            └─ soft_constraint_check | Component: SIPPS | Calls: 5407686 | Total: 11.6581s | Avg: 0.00ms | % of Parent: 1.6%
            └─ sipps_node_creation | Component: SIPPS | Calls: 5407686 | Total: 78.2447s | Avg: 0.01ms | % of Parent: 10.6%
      └─ cbs_iteration | Component: CBS | Calls: 74849 | Total: 8.2833s | Avg: 0.11ms | % of Parent: 1.0%
        └─ cbs_vertex_conflict | Component: CBS | Total: 0.0000s | % of Parent: 0.0%
        └─ build_solution | Component: CBS | Calls: 74849 | Total: 3.4766s | Avg: 0.05ms | % of Parent: 42.0%
        └─ detect_conflict | Component: CBS | Calls: 74849 | Total: 2.4970s | Avg: 0.03ms | % of Parent: 30.1%
    └─ pop_and_check_signature_in_sets | Component: ResPlaN | Calls: 224868 | Total: 0.8854s | Avg: 0.00ms | % of Parent: 0.1%
    └─ macroaction_loop | Component: ResPlaN | Calls: 18425 | Total: 4.9098s | Avg: 0.27ms | % of Parent: 0.4%
    └─ rcheck | Component: ResPlaN | Calls: 222951 | Total: 340.8186s | Avg: 1.53ms | % of Parent: 28.2%
  └─ extract_solution_from_predecessors | Component: ResPlaN | Calls: 1 | Total: 0.2369s | Avg: 236.90ms | % of Parent: 0.0%
</pre>


---
*Report generated on 2026-04-28 10:10:06*