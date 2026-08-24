import signal
import cProfile
import pstats
import io
import time

from src.domain.solver.solver_manager import solve_mapf
from src.utils.granular_profiler import get_profiler
from src.utils.bottleneck_analyzer import BottleneckAnalyzer

DEBUG = True
class TimeoutException(Exception):
    pass

def debug_print(message):
    if DEBUG:
        print(message)

def timeout_handler(signum, frame):
    raise TimeoutException()

def profile_code(func, *args, stdout_redirector=None, **kwargs):
    import cProfile, pstats, io, sys

    # Create a new profiler for each instance
    pr = cProfile.Profile()

    original_stdout = sys.stdout
    if stdout_redirector is not None:
        sys.stdout = stdout_redirector

    try:
        pr.clear()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
    finally:
        # Reset the profiler
        sys.setprofile(None)
        if stdout_redirector is not None:
            sys.stdout = original_stdout

    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats("cumulative")
    stats_dict = extract_stats(ps)

    return result, stats_dict

def solve_mapf_with_profiling(mapf_instance, robustness_params, search_params, stop_event=None):
    """
    Returns:
        (solution, profiling_stats_dict): where profiling_stats_dict contains granular data
    """
    profiler = get_profiler()
    profiler.reset()
    profiler.enabled = True
    
    import time
    start_time = time.time()
    
    try:
        # Run the algorithm
        result = solve_mapf(mapf_instance, robustness_params, search_params, stop_event=stop_event)
    finally:
        profiler.enabled = False
    
    elapsed_time = time.time() - start_time
    
    # Extract granular profiling data
    granular_data = profiler.get_report_dict()
    
    # Convert to stats format compatible with aggregate_granular_stats
    stats_dict = {}
    for func_name, stat in (granular_data or {}).items():
        if isinstance(stat, dict):
            stats_dict[func_name] = {
                'ncalls': stat.get('ncalls', 0),
                'cumtime': stat.get('cumtime', 0),
                'tottime': stat.get('tottime', 0),
                'mean_time': stat.get('mean_time', 0),
            }
    
    # Add elapsed time
    stats_dict['elapsed_time'] = elapsed_time
    
    return result, stats_dict


def solve_mapf_with_granular_profiling(mapf_instance, robustness_params, search_params, verbose=True, stop_event=None):
    """
    Execute solve_mapf with granular profiling and bottleneck analysis.
    
    Args:
        mapf_instance: MAPF problem instance
        robustness_params: Robustness parameters
        search_params: Search parameters
        verbose: If True, print reports
    
    Returns:
        (solution, {profiling_data, analysis})
    """
    profiler = get_profiler()
    profiler.reset()
    profiler.enabled = True
    
    start_time = time.time()
    
    if verbose:
        print("[Profiling] Starting granular profiling...")
    
    try:
        # Run the algorithm
        result = solve_mapf(mapf_instance, robustness_params, search_params, stop_event=stop_event)
    finally:
        profiler.enabled = False
    
    elapsed_time = time.time() - start_time
    
    if verbose:
        print("[Profiling] Profiling completed. Analyzing bottlenecks...")
    
    # Analyze bottlenecks
    analyzer = BottleneckAnalyzer()
    analysis = analyzer.analyze()
    
    # Add total time
    analysis['elapsed_time'] = elapsed_time
    
    if verbose:
        analyzer.print_analysis()
        profiler.print_report()
    
    return result, {
        'granular_stats': profiler.get_report_dict(),
        'analysis': analysis,
        'elapsed_time': elapsed_time
    }


def extract_stats(ps):
    functions_of_interest = {
        "resplan_mapf": None,
        "compute_plan_cbs": None,
        "low_level_search_cbs": None,
        "build_safe_interval_table": None,
        "populate_hard_constraints_agent": None,
        "populate_soft_constraints_agent": None,
        "area_capacity_soft_constraints_agent": None,
        "graph_modification_agent": None,
        "compute_goal_times_agent": None,
        "heuristic_computation": None,
        "root_compute_low_level_solution": None,
    }

    extracted = {
        key: {"ncalls": 0, "tottime": 0.0, "cumtime": 0.0}
        for key in functions_of_interest
    }

    for func, (cc, nc, tt, ct, callers) in ps.stats.items():
        filename, lineno, funcname = func
        if funcname in functions_of_interest:
            extracted[funcname] = {
                "ncalls": nc,
                "tottime": round(tt, 3),
                "cumtime": round(ct, 3),
                "mean_time": round(ct / nc, 5) if nc else 0,
            }
    return extracted


def generate_profiling_markdown(granular_stats, analysis, elapsed_time, instance_info=None):
    """
    Generate detailed markdown report from granular profiling.
    
    Args:
        granular_stats: Dictionary of granular statistics
        analysis: Bottleneck analysis from BottleneckAnalyzer
        elapsed_time: Total execution time
        instance_info: Dict with {'test_set', 'instance_idx', 'map_name', 'num_agents', 'k', 'm', 'h'}
    
    Returns:
        String with markdown report
    """
    report = []
    
    # Input validation
    if not isinstance(granular_stats, dict):
        granular_stats = {}
    if not isinstance(analysis, dict):
        analysis = {}
    if not isinstance(elapsed_time, (int, float)):
        elapsed_time = 0
    
    # Helper: Extract base function name (without _iteration_X, _agent_X, _step_X, etc.)
    def get_base_function_name(func_name):
        """Extract base function name removing suffixes like _iteration_X, _agent_X, _step_X"""
        if '_iteration_' in func_name:
            return func_name.split('_iteration_')[0] + '_iteration'
        elif '_step_' in func_name:
            return func_name.split('_step_')[0]
        elif '_agent_' in func_name:
            base = func_name.split('_agent_')[0]
            # For constraint population functions, return the base name
            if base in ['populate_hard_constraints', 'populate_soft_constraints', 
                       'area_capacity_soft_constraints', 'graph_modification', 'compute_goal_times',
                       'create_root_sipps_node', 'SIPPS_loop', 'build_safe_interval_table',
                       'SIPPS_node_expansion', 'hard_constraint_check', 'soft_constraint_check',
                       'sipps_node_creation']:
                return base
            return base + '_agent'
        else:
            return func_name
    
    # Helper: Categorize function into component
    def categorize_function(func_name):
        """Categorize a function into ResPlaN, CBS, SIPPS"""
        func_lower = func_name.lower()
        
        # ResPlaN components
        if ('resplan' in func_lower or 'pop_and_check_signature_in_sets' in func_lower or 
            'macroaction_loop' in func_lower or 'rcheck' in func_lower or 
            'extract_solution_from_predecessors' in func_lower):
            return 'ResPlaN'
        # Components of conflict-based search (excluding eliminated graph_setup operations)
        elif ('cbs' in func_lower or 'heuristic_computation' in func_lower or 
              'build_solution' in func_lower or 'detect_conflict' in func_lower or 
              'compute_plan_cbs' in func_lower):
            return 'CBS'
        # Components of low-level search (including root initialization)
        elif ('sipps' in func_lower or 'build_safe_interval' in func_lower or 
              'low_level_search_cbs' in func_lower or 'low_level' in func_lower or
              'populate_hard_constraints' in func_lower or 'populate_soft_constraints' in func_lower or
              'area_capacity_soft_constraints' in func_lower or 'graph_modification' in func_lower or
              'compute_goal_times' in func_lower or 'create_root_sipps_node' in func_lower or
              'hard_constraint_check' in func_lower or 'soft_constraint_check' in func_lower or
              'sipps_node_creation' in func_lower or 'sipps_node_expansion' in func_lower or
              'root_compute_low_level_solution' in func_lower or 'successor_generation' in func_lower or
              'goal_check' in func_lower or 'heap_pop' in func_lower or 'node_close' in func_lower or
              'successor_processing' in func_lower):
            return 'SIPPS'
        else:
            return 'ResPlaN'
    
    # Build function call hierarchy
    def get_function_hierarchy():
        """Define the call hierarchy of functions"""
        return {
            'ResPlaN': {
                'children': [
                    'resplan_iteration',
                    'extract_solution_from_predecessors'
                ]
            },
            'resplan_iteration': {
                'parent': 'ResPlaN',
                'children': ['compute_plan_cbs', 'pop_and_check_signature_in_sets', 'macroaction_loop', 'rcheck']
            },
            'compute_plan_cbs': {
                'parent': 'resplan_iteration',
                'children': ['heuristic_computation', 'root_compute_low_level_solution', 'cbs_iteration']
            },
            'root_compute_low_level_solution': {
                'parent': 'compute_plan_cbs',
                'children': []
            },
            'cbs_iteration': {
                'parent': 'compute_plan_cbs',
                'children': ['cbs_vertex_conflict', 'build_solution', 'detect_conflict']
            },
            'cbs_vertex_conflict': {
                'parent': 'cbs_iteration'
            },
            'build_solution': {
                'parent': 'cbs_iteration'
            },
            'detect_conflict': {
                'parent': 'cbs_iteration'
            },
            'low_level_search_cbs': {
                'parent': 'multi-context',
                'children': ['populate_hard_constraints', 'populate_soft_constraints', 'area_capacity_soft_constraints',
                            'graph_modification', 'build_safe_interval_table', 'compute_goal_times', 
                            'create_root_sipps_node', 'sipps_loop']
            },
            'populate_hard_constraints': {
                'parent': 'low_level_search_cbs'
            },
            'populate_soft_constraints': {
                'parent': 'low_level_search_cbs'
            },
            'area_capacity_soft_constraints': {
                'parent': 'low_level_search_cbs'
            },
            'graph_modification': {
                'parent': 'low_level_search_cbs'
            },
            'build_safe_interval_table': {
                'parent': 'low_level_search_cbs'
            },
            'compute_goal_times': {
                'parent': 'low_level_search_cbs'
            },
            'create_root_sipps_node': {
                'parent': 'low_level_search_cbs'
            },
            'sipps_loop': {
                'parent': 'low_level_search_cbs',
                'children': ['SIPPS_node_expansion', 'hard_constraint_check', 'soft_constraint_check', 'sipps_node_creation']
            },
            'SIPPS_node_expansion': {
                'parent': 'sipps_loop'
            },
            'hard_constraint_check': {
                'parent': 'sipps_loop'
            },
            'soft_constraint_check': {
                'parent': 'sipps_loop'
            },
            'sipps_node_creation': {
                'parent': 'sipps_loop'
            },
            'heuristic_computation': {
                'parent': 'compute_plan_cbs'
            },
            'pop_and_check_signature_in_sets': {
                'parent': 'resplan_iteration'
            },
            'macroaction_loop': {
                'parent': 'resplan_iteration'
            },
            'rcheck': {
                'parent': 'resplan_iteration'
            },
            'extract_solution_from_predecessors': {
                'parent': 'ResPlaN'
            }
        }
    
    # Aggregation of related functions
    aggregated_stats = {}
    for func_name, stat in granular_stats.items():
        if not isinstance(stat, dict):
            continue
        
        base_name = get_base_function_name(func_name)
        if base_name not in aggregated_stats:
            aggregated_stats[base_name] = {
                'cumtime': 0,
                'exclusive_time': 0,
                'child_time': 0,
                'ncalls': 0,
                'times': []  # List of individual times to calculate min/max/avg
            }
        
        aggregated_stats[base_name]['cumtime'] += stat.get('cumtime', 0)
        aggregated_stats[base_name]['exclusive_time'] += stat.get('exclusive_time', stat.get('cumtime', 0))
        aggregated_stats[base_name]['child_time'] += stat.get('child_time', 0)
        aggregated_stats[base_name]['ncalls'] += stat.get('ncalls', 0)
        
        # Collect individual times if available
        if stat.get('ncalls', 0) > 0:
            # Calculate time per single call
            time_per_call = stat.get('cumtime', 0) / stat.get('ncalls', 0)
            aggregated_stats[base_name]['times'].extend([time_per_call] * stat.get('ncalls', 0))
    
    # Add averages and components
    for base_name, agg in aggregated_stats.items():
        if agg['ncalls'] > 0:
            agg['mean_time'] = agg['cumtime'] / agg['ncalls']
            agg['mean_exclusive'] = agg['exclusive_time'] / agg['ncalls']
        else:
            agg['mean_time'] = 0
            agg['mean_exclusive'] = 0
        agg['component'] = categorize_function(base_name)
    
    # Recalculate component breakdown with aggregate statistics
    components_breakdown = {'ResPlaN': {'time': 0, 'exclusive': 0, 'calls': 0},
                           'CBS': {'time': 0, 'exclusive': 0, 'calls': 0},
                           'SIPPS': {'time': 0, 'exclusive': 0, 'calls': 0}}
    
    for base_name, agg in aggregated_stats.items():
        component = categorize_function(base_name)
        components_breakdown[component]['time'] += agg['cumtime']
        components_breakdown[component]['exclusive'] += agg['exclusive_time']
        components_breakdown[component]['calls'] += agg['ncalls']
    
    # Header
    report.append("# Profiling Report - ResPlaN MAPF\n")
    
    if instance_info:
        report.append("## Instance Information\n")
        report.append(f"- **Test Set**: {instance_info.get('test_set', 'N/A')}")
        report.append(f"- **Instance Index**: {instance_info.get('instance_idx', 'N/A')}")
        report.append(f"- **Map**: {instance_info.get('map_name', 'N/A')}")
        report.append(f"- **Agents**: {instance_info.get('num_agents', 'N/A')}")
        report.append(f"- **Parameters**: k={instance_info.get('k', 'N/A')}, m={instance_info.get('m', 'N/A')}, h={instance_info.get('h', 'N/A')}")
        failure_types = instance_info.get('failure_types', [])
        failure_types_str = ', '.join(failure_types) if failure_types else 'None'
        report.append(f"- **Failure Types**: {failure_types_str}\n")
    
    # Execution Time with Wall-Clock vs Profiled Analysis
    report.append("## Execution Summary\n")
    
    # Calculate totals
    total_profiled_inclusive = sum(agg.get('cumtime', 0) for agg in aggregated_stats.values())
    total_profiled_exclusive = sum(agg.get('exclusive_time', 0) for agg in aggregated_stats.values())
    
    report.append(f"- **Total Wall-Clock Time**: {elapsed_time:.4f}s (actual real time)")
    report.append(f"- **Total Profiled Time (Inclusive)**: {total_profiled_inclusive:.4f}s (sum of all sections)")
    report.append(f"- **Total Exclusive Time**: {total_profiled_exclusive:.4f}s (no nesting counted)")
    
    # Calculate unaccounted time
    unaccounted = elapsed_time - total_profiled_exclusive
    unaccounted_pct = (unaccounted / elapsed_time * 100) if elapsed_time > 0 else 0
    
    report.append(f"- **Unaccounted Time**: {unaccounted:.4f}s ({unaccounted_pct:.1f}%)")
    
    # Overhead analysis
    if total_profiled_exclusive > 0:
        nesting_inflation = total_profiled_inclusive / total_profiled_exclusive
        report.append(f"- **Nesting Inflation Factor**: {nesting_inflation:.2f}× (due to nested profiling sections)\n")
    else:
        report.append()
    
    report.append("*Note: Unaccounted time includes untracked code sections and profiling overhead.*\n")
    
    # Component Breakdown (with inclusive and exclusive)
    report.append("## Component Breakdown\n")
    report.append("| Component | Time (s) | Exclusive (s) | Calls | Avg Time (ms) | % of Exclusive |")
    report.append("|-----------|----------|---------------|-------|---------------|----------------|")
    
    total_time = sum(comp['time'] for comp in components_breakdown.values())
    total_exclusive = sum(comp.get('exclusive', comp['time']) for comp in components_breakdown.values())
    
    for component_name in ['ResPlaN', 'CBS', 'SIPPS']:
        comp_data = components_breakdown[component_name]
        time_s = comp_data['time']
        excl_s = comp_data.get('exclusive', time_s)  # Fallback to inclusive if not calculated
        calls = comp_data['calls']
        avg_ms = (excl_s / calls * 1000) if calls > 0 else 0
        pct = (excl_s / total_exclusive * 100) if total_exclusive > 0 else 0
        report.append(f"| {component_name} | {time_s:.4f} | {excl_s:.4f} | {calls} | {avg_ms:.2f} | {pct:.1f}% |")
    report.append("")
    
    # Top 10 Time-Consuming Functions (by exclusive time)
    report.append("## Top 10 Time-Consuming Functions (Exclusive Time)\n")
    report.append("| Function | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of Total |")
    report.append("|----------|-------|----------------|----------------|---------------|------------|")
    
    all_stats_sorted = sorted(
        aggregated_stats.items(),
        key=lambda x: x[1].get('exclusive_time', x[1]['cumtime']),
        reverse=True
    )
    
    for i, (func_name, agg) in enumerate(all_stats_sorted[:10]):
        try:
            inc_t = agg['cumtime']
            excl_t = agg.get('exclusive_time', inc_t)
            calls = agg['ncalls']
            avg_excl_ms = (excl_t / calls * 1000) if calls > 0 else 0
            pct = (excl_t / total_exclusive * 100) if total_exclusive > 0 else 0
            report.append(f"| {func_name} | {calls} | {inc_t:.4f} | {excl_t:.4f} | {avg_excl_ms:.2f} | {pct:.1f}% |")
        except (TypeError, ValueError) as e:
            report.append(f"| {func_name} | ERROR | ERROR | ERROR | ERROR | ERROR |")
    report.append("")
    
    # SIPPS Loop Operation Breakdown
    report.append("## SIPPS Loop Operation Breakdown\n")
    sipps_ops = {k: v for k, v in aggregated_stats.items() if 'sipps_' in k.lower()}
    sipps_ops_sorted = sorted(sipps_ops.items(), key=lambda x: x[1].get('exclusive_time', x[1]['cumtime']), reverse=True)
    
    if sipps_ops_sorted:
        report.append("| Operation | Calls | Inclusive (s) | Exclusive (s) | Avg Excl (ms) | % of SIPPS |")
        report.append("|-----------|-------|----------------|----------------|---------------|-----------|")
        
        sipps_excl_total = sum(v.get('exclusive_time', v['cumtime']) for v in sipps_ops.values())
        
        for op_name, op_stats in sipps_ops_sorted:
            exc_t = op_stats.get('exclusive_time', op_stats['cumtime'])
            inc_t = op_stats['cumtime']
            calls = op_stats['ncalls']
            avg_ms = (exc_t / calls * 1000) if calls > 0 else 0
            pct = (exc_t / sipps_excl_total * 100) if sipps_excl_total > 0 else 0
            report.append(f"| {op_name} | {calls} | {inc_t:.4f} | {exc_t:.4f} | {avg_ms:.2f} | {pct:.1f}% |")
        report.append("")
    
    # Performance Notes
    report.append("## Performance Notes\n")
    report.append("**Time Attribution**:\n")
    report.append("- **Inclusive Time**: Total time a section ran (including time in nested children)")
    report.append("- **Exclusive Time**: Time spent directly in that section (excluding children)")
    report.append("- **Unaccounted**: Wall-clock - Exclusive = overhead and untracked code\n")
    
    report.append("**Constraint Checking Costs** (if available):\n")
    for op_name, op_stats in sipps_ops_sorted[:3]:
        if 'constraint' in op_name.lower():
            exc_t = op_stats.get('exclusive_time', op_stats['cumtime'])
            calls = op_stats['ncalls']
            avg_ms = (exc_t / calls * 1000) if calls > 0 else 0
            report.append(f"- **{op_name}**: {avg_ms:.3f}ms per call ({calls:,} calls)\n")
    
    # Note about multi-context functions
    report.append("**Note on `low_level_search_cbs`**: This function is called from multiple contexts:")
    report.append("- During root CBS initialization (~15-20% of calls)")
    report.append("- During CBS conflict resolution iterations (~80-85% of calls)")
    report.append("The time reported includes ALL calls aggregated across both contexts.\n")
    
    # Detailed Granular Statistics (Hierarchical Tree)
    report.append("## Detailed Granular Statistics\n")
    report.append("<pre style=\"overflow-x: auto; white-space: pre;\">")
    
    hierarchy = get_function_hierarchy()
    
    # Helper: Calculate total time for a node by summing its children
    def get_node_total_time(node_name):
        """Get total time for a node. If node has no direct data, sum its children."""
        if node_name in aggregated_stats:
            return aggregated_stats[node_name]['cumtime']
        
        # If not in stats, calculate from children
        total = 0
        if node_name in hierarchy and 'children' in hierarchy[node_name]:
            for child_name in hierarchy[node_name]['children']:
                total += get_node_total_time(child_name)
        return total
    
    # Helper: Recursively print tree
    def print_tree_node(node_name, parent_name=None, indent=0, prefix="", parent_time=None):
        """Print a node in the tree with its stats"""
        # Special handling for pseudo-root nodes like 'ResPlaN'
        if node_name == 'ResPlaN' and parent_name is None:
            # For pseudo-root ResPlaN as the main root
            # The time of ResPlaN is the elapsed_time, representing 100% of execution
            report.append(f"{node_name} | Component: ResPlaN | Total: {elapsed_time:.4f}s | % of Total: 100.0%")
            
            # Process children directly (resplan_iteration and extract_solution_from_predecessors as siblings)
            if node_name in hierarchy and 'children' in hierarchy[node_name]:
                for child_name in hierarchy[node_name]['children']:
                    print_tree_node(child_name, node_name, indent + 1, prefix + "  ", elapsed_time)
            return
        
        # Try to find the node in aggregated_stats (case-insensitive)
        stats = None
        for key in aggregated_stats:
            if key.lower() == node_name.lower():
                stats = aggregated_stats[key]
                break
        
        # Get total time for this node (from stats or calculated from children)
        if stats:
            # Node has direct data
            calls = stats['ncalls']
            total = stats['cumtime']
            avg = stats['mean_time'] * 1000 if stats['ncalls'] > 0 else 0
            component = stats['component']
            has_direct_data = True
        else:
            # Node doesn't have direct data, calculate from children
            total = get_node_total_time(node_name)
            calls = 0
            avg = 0
            component = categorize_function(node_name)  # Still categorize even without direct data
            has_direct_data = False
        
        # Calculate percentage
        if parent_time and parent_time > 0:
            percentage = (total / parent_time) * 100
            pct_str = f"{percentage:.1f}%"
        elif parent_name is None:  # Root node (extract_solution_from_predecessors)
            percentage = (total / elapsed_time) * 100 if elapsed_time > 0 else 0
            pct_str = f"{percentage:.1f}%"
        else:
            pct_str = "N/A"
        
        # Format and print - all on one line
        connector = "  " * (indent - 1) + "  └─ "
        line = f"{connector}{node_name}"
        
        if has_direct_data:
            line += f" | Component: {component} | Calls: {calls} | Total: {total:.4f}s | Avg: {avg:.2f}ms | % of Parent: {pct_str}"
        else:
            line += f" | Component: {component} | Total: {total:.4f}s | % of Parent: {pct_str}"
        
        report.append(line)
        
        # Process children if they exist
        if node_name in hierarchy and 'children' in hierarchy[node_name]:
            for child_name in hierarchy[node_name]['children']:
                print_tree_node(child_name, node_name, indent + 1, prefix + "  ", total)
    
    # Print main ResPlaN tree (includes all children including extract_solution_from_predecessors)
    print_tree_node('ResPlaN', None, 0, "")
    
    report.append("</pre>")
    report.append("")
    report.append("")
    report.append("---")
    report.append(f"*Report generated on {time.strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return "\n".join(report)


def save_profiling_report(markdown_content, test_set, instance_idx, map_name):
    """
    Save markdown report to a dedicated directory.
    
    Args:
        markdown_content: Markdown report content
        test_set: Name of the test set
        instance_idx: Index of the instance
        map_name: Name of the map
    
    Returns:
        Path to the saved file
    """
    import os
    from pathlib import Path
    
    # Create directory if it doesn't exist
    reports_dir = Path("data/profiling_reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    
    # Sanitize map name
    safe_map_name = map_name.replace("/", "_").replace("\\", "_")
    
    # Name the file
    filename = f"profiling_{test_set}_idx{instance_idx:03d}_{safe_map_name}_{timestamp}.md"
    filepath = reports_dir / filename
    
    # Save the file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return str(filepath)