import os
import csv

def aggregate_granular_stats(granular_stats):
    """
    Convert granular statistics to CSV format.
    Aggregate data by component (ResPlaN, CBS, SIPPS)
    """
    aggregated = {}
    
    if not granular_stats:
        return aggregated
    
    # Initialize counters for components
    components = {
        'resplan_mapf': {'ncalls': 0, 'cumtime': 0, 'mean_time': 0},
        'compute_plan_cbs': {'ncalls': 0, 'cumtime': 0, 'mean_time': 0},
        'low_level_search_cbs': {'ncalls': 0, 'cumtime': 0, 'mean_time': 0},
        'build_safe_interval_table': {'ncalls': 0, 'cumtime': 0, 'mean_time': 0},
    }
    
    # Iterate over granular statistics
    call_times = {
        'resplan_mapf': [],
        'compute_plan_cbs': [],
        'low_level_search_cbs': [],
        'build_safe_interval_table': [],
    }
    
    for func_name, stats in granular_stats.items():
        if stats is None:
            continue
        
        ncalls = stats.get('ncalls', 0)
        cumtime = stats.get('cumtime', 0)
        
        # Categorize functions with improved logic for specific functions
        component = None
        
        if 'resplan_iteration' in func_name or 'resplan' in func_name.lower():
            component = 'resplan_mapf'
        elif 'pop_and_check_signature_in_sets' in func_name or 'macroaction_loop' in func_name or 'extract_solution_from_predecessors' in func_name:
            component = 'resplan_mapf'  # High-level ResPlaN operations
        elif 'rcheck' in func_name:
            component = 'resplan_mapf'  # Part of ResPlaN resilience check
        elif 'heuristic_computation' in func_name or 'build_solution' in func_name or 'detect_conflict' in func_name or 'CBS' in func_name or 'compute_plan_cbs' in func_name:
            component = 'compute_plan_cbs'
        elif 'CBS_low_level_down_state' in func_name or 'CBS_vertex_conflict' in func_name or 'CBS_edge_conflict' in func_name:
            component = 'compute_plan_cbs'  # Sub-operations of CBS
        elif 'SIPPS' in func_name or 'low_level' in func_name or 'build_safe' in func_name:
            component = 'low_level_search_cbs'
        else:
            # Default: try to infer from function name patterns
            continue
        
        if component:
            # Aggregate
            components[component]['ncalls'] += ncalls
            components[component]['cumtime'] += cumtime
            
            # Save individual times to calculate correct average
            if ncalls > 0:
                call_times[component].append((cumtime, ncalls))
    
    # Calculate correct averages
    for component, data in call_times.items():
        if data:
            total_time = sum(t for t, _ in data)
            total_calls = sum(c for _, c in data)
            if total_calls > 0:
                components[component]['mean_time'] = total_time / total_calls
    
    return components


def build_solutions_csv(instances, robustness_params, solutions, selected_set, timing_stats, timed_out_flags):
    filename = os.environ.get("RESULTS_CSV_PATH", "results.csv")
    file_exists = os.path.exists(filename)

    fieldnames = [
        "test_case_name", "map", "num_agents", "total cells", "percentage of available cells",
        "R_up", "R_down", "success", "timelimit_reached", "k", "m", "h",
        "k-res_solution_cost", "0-res_sol_cost", "delta %", "failure types",
        "time_resplan", "calls_compute_plan_cbs", "time_compute_plan_cbs", "mean_compute_plan_cbs",
        "calls_low_level_search_cbs", "time_low_level_search_cbs", "mean_low_level_search_cbs",
        "calls_safe_interval_table", "time_safe_interval_table", "mean_safe_interval_table",
        "elapsed_time", "cbs_percentage", "sipps_percentage",
        "cbs_total_conflicts", "cbs_non_resilient_states", "starts", "goals"
    ]


    if not file_exists:
        with open(filename, mode="w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, "rb") as f:
            f.seek(-1, os.SEEK_END)
            if f.read(1) != b"\n":
                with open(filename, "a", newline="") as f_append:
                    f_append.write("\n")

    for instance, solution, stats, timeout_flag in zip(instances, solutions, timing_stats, timed_out_flags):
        map_name, inst_starts, inst_goals = instance[0], instance[1], instance[2]

        # Safe computation of map info with error handling
        try:
            total_cells, percentage_avail_cells = compute_map_info(map_name)
        except Exception as e:
            print(f"Warning: failed to compute map info for {map_name}: {e}")
            total_cells, percentage_avail_cells = 0, 0

        # Supporta sia il vecchio formato (cProfile) che il nuovo (granulare)
        if isinstance(stats, dict) and all(isinstance(v, dict) for v in stats.values()):
            # Nuovo formato: statistiche granulari
            aggregated = aggregate_granular_stats(stats)
        else:
            # Vecchio formato: statistiche cProfile
            aggregated = stats

        # Estrai counters CBS (presenti nel dict stats al top-level)
        _counters = stats.get('_counters', {}) if isinstance(stats, dict) else {}

        def safe_stat(fn, key):
            return aggregated.get(fn, {}).get(key, 0) if isinstance(aggregated.get(fn), dict) else 0

        # Calcola percentuali
        cbs_time = safe_stat("compute_plan_cbs", "cumtime")
        sipps_time = safe_stat("low_level_search_cbs", "cumtime")
        resplan_time = safe_stat("resplan_mapf", "cumtime")
        total_time = cbs_time + sipps_time + resplan_time
        
        cbs_pct = round((cbs_time / total_time * 100), 2) if total_time > 0 else 0
        sipps_pct = round((sipps_time / total_time * 100), 2) if total_time > 0 else 0

        row = {
            "test_case_name": selected_set,
            "map": map_name,
            "num_agents": len(inst_starts),
            "total cells": total_cells,
            "percentage of available cells": percentage_avail_cells,
            "R_up": len(solution.R_up),
            "R_down": len(solution.R_down),
            "success": solution.tau_states is not None,
            "timelimit_reached": timeout_flag,
            "k": robustness_params.k,
            "m": robustness_params.m,
            "h": robustness_params.h,
            "k-res_solution_cost": solution.resilient_cost if solution.tau_states is not None else None,
            "0-res_sol_cost": solution.cbs_cost if solution.cbs_cost is not None else None,
            "delta %": round(100 * (solution.resilient_cost - solution.cbs_cost) / solution.cbs_cost, 2) if solution.resilient_cost is not None and solution.cbs_cost is not None else None,
            "failure types": robustness_params.selected_failure_types,
            "time_resplan": safe_stat("resplan_mapf", "cumtime"),
            "calls_compute_plan_cbs": safe_stat("compute_plan_cbs", "ncalls"),
            "time_compute_plan_cbs": safe_stat("compute_plan_cbs", "cumtime"),
            "mean_compute_plan_cbs": safe_stat("compute_plan_cbs", "mean_time"),
            "calls_low_level_search_cbs": safe_stat("low_level_search_cbs", "ncalls"),
            "time_low_level_search_cbs": safe_stat("low_level_search_cbs", "cumtime"),
            "mean_low_level_search_cbs": safe_stat("low_level_search_cbs", "mean_time"),
            "calls_safe_interval_table": safe_stat("build_safe_interval_table", "ncalls"),
            "time_safe_interval_table": safe_stat("build_safe_interval_table", "cumtime"),
            "mean_safe_interval_table": safe_stat("build_safe_interval_table", "mean_time"),
            "elapsed_time": stats.get("elapsed_time", None) if isinstance(stats, dict) else None,
            "cbs_percentage": cbs_pct,
            "sipps_percentage": sipps_pct,
            "cbs_total_conflicts": _counters.get('cbs_total_conflicts', 0),
            "cbs_non_resilient_states": _counters.get('cbs_non_resilient_states', 0),
            "starts": inst_starts,
            "goals": inst_goals,
        }

        with open(filename, mode="a", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writerow(row)

def compute_map_info(map_name):
    from src.utils.map_handler import load_map, build_graph

    grid = load_map(map_name)
    graph = build_graph(grid)

    total_cells = sum(len(row) for row in grid)
    free_cells = graph.number_of_nodes()
    percentage_avail_cells = round(100 * free_cells / total_cells, 2)

    return total_cells, percentage_avail_cells

