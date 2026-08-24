"""
Batch Profiling Analysis Script
================================
Esegue istanze multiple times, raccoglie dati di granular profiling,
calcola le medie e genera report markdown per ciascuna istanza.

Nessuna interazione GUI richiesta. I parametri sono configurati direttamente nel file.
"""

import os
import sys
import pickle
import time
import threading
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Aggiungi il workspace root al path (serve per importare il package `src`)
WORKSPACE_ROOT = Path(__file__).parent.parent  # Punta alla root del progetto
sys.path.insert(0, str(WORKSPACE_ROOT))

from src.domain.generation import TEST_INSTANCES_DIR
from src.utils.map_handler import load_map, build_graph
from src.domain.MAPFInstance import MAPFInstance, RobustnessParams, SearchParams
from src.utils.profiling import solve_mapf_with_granular_profiling


# ==============================================================================
# CONFIGURAZIONE - Modifica questi parametri
# ==============================================================================

# Istanze da elaborare direttamente (lista di dizionari)
# Formato: {"grid": "nome_mappa", "start_positions": [[x,y], ...], "goal_positions": [[x,y], ...], "k": ..., "m": ..., "h": ..., "selected_failtypes": [...]}
INSTANCES = [
    {
        "grid": "random16_2.map",
        "start_positions": [[1, 2],[12,3]],
        "goal_positions": [[0, 14],[4,11]],
        "k": 2,
        "m": 2,
        "h": 1,
        "selected_failtypes": ["individual","topw"],
    },
    {
        "grid": "random18_3.map", 
        "start_positions": [[8, 8], [16, 1]],
        "goal_positions": [[16, 16], [8, 8]],
        "k": 2,
        "m": 1,
        "h": 2,
        "selected_failtypes": ["high-level"],
    },
    {
        "grid": "medium_free.map",  
        "start_positions": [[2, 2], [2, 17]],
        "goal_positions": [[18, 18], [17, 2]],
        "k": 2,
        "m": 2,
        "h": 1,
        "selected_failtypes": ["individual"],
    },
    {
        "grid": "random21.map", 
        "start_positions": [[1, 1], [20, 5]],
        "goal_positions": [[19, 19], [11, 11]],
        "k": 2,
        "m": 2,
        "h": 1,
        "selected_failtypes": ["tops"],
    },
]

# Indici delle istanze da elaborare (0-indexed)
INSTANCE_INDICES = [0, 1, 2, 3]

# Numero di volte che ciascuna istanza deve essere eseguita
NUM_RUNS = 1

# Timeout per ogni esecuzione in secondi (300 sec = 5 minuti)
TIMEOUT_PER_RUN = 300  # 5 minuti

# Directory di output per i report markdown
OUTPUT_DIR = WORKSPACE_ROOT / "data/batch_profiling_reports"

# ==============================================================================
# FINE CONFIGURAZIONE
# ==============================================================================


def load_test_instances(test_set_name: str):
    """Carica il file pickle con le istanze di test."""
    filepath = os.path.join(TEST_INSTANCES_DIR, test_set_name)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, "rb") as f:
        instances = pickle.load(f)
    return instances


def run_single_instance(map_name: str, starts: list, goals: list, 
                       robustness_params: RobustnessParams, 
                       verbose: bool = False) -> tuple:
    """
    Esegue una singola istanza con granular profiling.
    
    Returns:
        (solution, profiling_data)
    """
    try:
        grid = load_map(map_name)
        # Converti liste di liste in tuple di tuple
        starts = [tuple(s) for s in starts]
        goals = [tuple(g) for g in goals]
        mapf_instance = MAPFInstance(build_graph(grid, len(starts)), starts, goals)
        
        # Inizializza i parametri di ricerca
        init_failed_actions = tuple(frozenset() for _ in starts)
        init_failures = [0] * len(starts)
        r_up, r_down, predecessors, resilient_macroactions = set(), set(), dict(), dict()
        search_params = SearchParams(
            init_failed_actions, init_failures, 
            r_up, r_down, predecessors, resilient_macroactions
        )
        
        # Esegui con granular profiling
        solution, profiling_data = solve_mapf_with_granular_profiling(
            mapf_instance, robustness_params, search_params, verbose=verbose
        )
        
        return solution, profiling_data
    except Exception as e:
        print(f"Error running instance: {e}")
        raise


def run_with_timeout(map_name: str, starts: list, goals: list,
                     robustness_params: RobustnessParams,
                     timeout_sec: int) -> tuple:
    """
    Esegue una singola istanza con timeout usando threading.
    
    Returns:
        (success: bool, solution, profiling_data): success=False on timeout
    """
    result = {"success": False, "solution": None, "profiling_data": None, "error": None}
    
    def worker():
        try:
            solution, profiling_data = run_single_instance(
                map_name, starts, goals, robustness_params, False
            )
            result["success"] = True
            result["solution"] = solution
            result["profiling_data"] = profiling_data
        except Exception as e:
            result["error"] = str(e)
    
    # Run in daemon thread so it doesn't block program exit
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout_sec)
    
    # If thread is still alive after timeout, it exceeded limit
    if thread.is_alive():
        return (False, None, None)
    
    # Thread completed - check result
    if result["success"]:
        return (True, result["solution"], result["profiling_data"])
    else:
        return (False, None, None)


def aggregate_profiling_data(profiling_runs: list) -> dict:
    """
    Aggrega i dati di profiling da molteplici run.
    Calcola medie, min, max per ciascuna funzione.
    Raggruppa funzioni simili (es: resplan_iteration_1, resplan_iteration_2 -> resplan_iteration)
    
    Args:
        profiling_runs: Lista di dizionari profiling_data da molteplici run
    
    Returns:
        Dizionario aggregato con statistiche medie
    """
    if not profiling_runs:
        return {}
    
    def get_base_function_name(func_name: str) -> str:
        """Estrae il nome base rimuovendo suffissi numerici (_iteration_X, _agent_X, ecc)"""
        # Rimuovi suffissi come _iteration_123, _agent_0, _step_5, etc
        if '_iteration_' in func_name:
            return func_name.split('_iteration_')[0] + '_iteration'
        elif '_agent_' in func_name:
            return func_name.split('_agent_')[0] + '_agent'
        elif '_step_' in func_name:
            return func_name.split('_step_')[0] + '_step'
        else:
            return func_name
    
    # Raccogli tutti i nomi di funzioni unici
    all_functions = set()
    for profiling_data in profiling_runs:
        if 'granular_stats' in profiling_data:
            all_functions.update(profiling_data['granular_stats'].keys())
    
    # Raggruppami per base_function_name
    aggregated_by_base = {}
    
    for func_name in all_functions:
        base_name = get_base_function_name(func_name)
        
        if base_name not in aggregated_by_base:
            aggregated_by_base[base_name] = {
                'times': [],
                'calls': []
            }
        
        for profiling_data in profiling_runs:
            if 'granular_stats' in profiling_data:
                stats = profiling_data['granular_stats']
                if func_name in stats:
                    stat = stats[func_name]
                    aggregated_by_base[base_name]['times'].append(stat.get('cumtime', 0))
                    aggregated_by_base[base_name]['calls'].append(stat.get('ncalls', 0))
    
    # Calcola statistiche per base function
    aggregated = {}
    for base_name, data in aggregated_by_base.items():
        if data['times']:
            aggregated[base_name] = {
                'avg_cumtime': sum(data['times']) / len(data['times']),
                'min_cumtime': min(data['times']),
                'max_cumtime': max(data['times']),
                'avg_ncalls': sum(data['calls']) / len(data['calls']) if data['calls'] else 0,
                'num_runs': len(data['times'])
            }
    
    return aggregated


def generate_markdown_report(instance_idx: int, map_name: str, starts: list, 
                            goals: list, robustness_params: RobustnessParams,
                            aggregated_stats: dict, num_runs: int,
                            total_elapsed_times: list) -> str:
    """
    Genera un report markdown con le statistiche aggregate.
    
    Args:
        instance_idx: Indice dell'istanza
        map_name: Nome della mappa
        starts: Lista dei punti di inizio per gli agenti
        goals: Lista dei punti di goal per gli agenti
        robustness_params: Parametri di robustness
        aggregated_stats: Statistiche aggregate da molteplici run
        num_runs: Numero di run eseguiti
        total_elapsed_times: Lista dei tempi elapsed totali
    
    Returns:
        String con il markdown report
    """
    report = []
    
    # Header
    report.append("# Batch Profiling Analysis Report\n")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    # Instance Information
    report.append("## Instance Information\n")
    report.append(f"- **Instance Index**: {instance_idx}")
    report.append(f"- **Map**: {map_name}")
    report.append(f"- **Number of Agents**: {len(starts)}")
    report.append(f"- **Number of Runs**: {num_runs}\n")
    
    # Robustness Parameters
    report.append("## Robustness Parameters\n")
    report.append(f"- **k (number of failures)**: {robustness_params.k}")
    report.append(f"- **m (max agents affected)**: {robustness_params.m}")
    report.append(f"- **h (search depth)**: {robustness_params.h}")
    failure_types_str = ', '.join(robustness_params.selected_failure_types)
    report.append(f"- **Failure Types**: {failure_types_str}\n")
    
    # Execution Summary
    if total_elapsed_times:
        avg_time = sum(total_elapsed_times) / len(total_elapsed_times)
        min_time = min(total_elapsed_times)
        max_time = max(total_elapsed_times)
        
        report.append("## Execution Summary\n")
        report.append("| Metric | Value |")
        report.append("|--------|-------|")
        report.append(f"| Average Total Time | {avg_time:.4f} s |")
        report.append(f"| Min Total Time | {min_time:.4f} s |")
        report.append(f"| Max Total Time | {max_time:.4f} s |")
        report.append(f"| Std Dev | {_calculate_stddev(total_elapsed_times):.4f} s |\n")
    
    # Granular Profiling Results
    report.append("## Granular Profiling Results (Averaged over {} runs)\n".format(num_runs))
    
    if aggregated_stats:
        # Ordina per tempo total medio
        sorted_functions = sorted(
            aggregated_stats.items(),
            key=lambda x: x[1]['avg_cumtime'],
            reverse=True
        )
        
        report.append("| Function | Avg Cumtime (s) | Min (s) | Max (s) | Avg Calls | Std Dev |")
        report.append("|----------|-----------------|---------|---------|-----------|---------|")
        
        for func_name, stats in sorted_functions:
            avg_time = stats['avg_cumtime']
            min_time = stats['min_cumtime']
            max_time = stats['max_cumtime']
            avg_calls = stats['avg_ncalls']
            stddev = _calculate_stddev_for_function(func_name, aggregated_stats)
            
            report.append(
                f"| {func_name} | {avg_time:.6f} | {min_time:.6f} | {max_time:.6f} | "
                f"{avg_calls:.1f} | {stddev:.6f} |"
            )
        
        report.append("")
        
        # Top 5 bottlenecks
        report.append("## Top 5 Bottlenecks\n")
        for i, (func_name, stats) in enumerate(sorted_functions[:5], 1):
            percentage = (stats['avg_cumtime'] / sum(s['avg_cumtime'] for s in aggregated_stats.values()) * 100)
            report.append(f"{i}. **{func_name}**: {stats['avg_cumtime']:.6f}s ({percentage:.1f}%)")
        report.append("")
    else:
        report.append("No profiling data collected.\n")
    
    report.append("---")
    report.append("*Report generated by batch_profiling_analysis.py*")
    
    return "\n".join(report)


def _calculate_stddev(values: list) -> float:
    """Calcola la deviazione standard."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    return variance ** 0.5


def _calculate_stddev_for_function(func_name: str, aggregated_stats: dict) -> float:
    """Placeholder per stddev function-specific (potrebbe essere ampliato)."""
    # Ignoriamo per ora, potrebbe essere calcolato tracciando i dati grezzi
    return 0.0


def create_output_directory():
    """Crea la directory di output se non esiste."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_report(report_content: str, instance_idx: int, test_set_name: str) -> Path:
    """
    Salva il report markdown in un file.
    
    Returns:
        Path al file salvato
    """
    test_set_clean = test_set_name.replace(".pkl", "").replace(".pickle", "")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"batch_profiling_{test_set_clean}_inst{instance_idx:03d}_{timestamp}.md"
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    return filepath


def main():
    """Funzione principale."""
    print("="*80)
    print("Batch Profiling Analysis")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Total Instances: {len(INSTANCES)}")
    print(f"  Instance Indices: {INSTANCE_INDICES}")
    print(f"  Runs per Instance: {NUM_RUNS}")
    print(f"  Output Directory: {OUTPUT_DIR}\n")
    
    # Crea output directory
    create_output_directory()
    
    # Processa istanze selezionate
    for instance_idx in INSTANCE_INDICES:
        if instance_idx >= len(INSTANCES):
            print(f"⚠ Instance index {instance_idx} out of range (max: {len(INSTANCES) - 1})")
            continue
        
        print(f"\n{'='*80}")
        print(f"Processing Instance {instance_idx}")
        print(f"{'='*80}")
        
        instance_data = INSTANCES[instance_idx]
        map_name = instance_data["grid"]
        starts = instance_data["start_positions"]
        goals = instance_data["goal_positions"]
        k = instance_data["k"]
        m = instance_data["m"]
        h = instance_data["h"]
        failure_types = instance_data["selected_failtypes"]
        
        # Crea parametri robustness specifici per questa istanza
        instance_robustness_params = RobustnessParams(k, m, h, failure_types)
        
        print(f"Map: {map_name}")
        print(f"Agents: {len(starts)}")
        print(f"Parameters: k={k}, m={m}, h={h}, failures={failure_types}")
        print(f"Executing {NUM_RUNS} times...\n")
        
        # Esegui l'istanza NUM_RUNS volte con timeout
        profiling_runs = []
        total_elapsed_times = []
        successful_runs = 0
        
        for run_idx in range(NUM_RUNS):
            start_time = time.time()
            try:
                success, solution, profiling_data = run_with_timeout(
                    map_name, starts, goals, instance_robustness_params, TIMEOUT_PER_RUN
                )
                elapsed_time = time.time() - start_time
                
                if success:
                    profiling_runs.append(profiling_data)
                    total_elapsed_times.append(elapsed_time)
                    successful_runs += 1
                    print(f"  Run {run_idx + 1}/{NUM_RUNS}: {elapsed_time:.2f}s ✓")
                else:
                    print(f"  Run {run_idx + 1}/{NUM_RUNS}: TIMEOUT (>{TIMEOUT_PER_RUN}s) ✗")
                    
            except Exception as e:
                elapsed_time = time.time() - start_time
                print(f"  Run {run_idx + 1}/{NUM_RUNS}: Error - {e} ✗")
        
        print(f"\n✓ Completed {successful_runs}/{NUM_RUNS} successful runs")
        
        # Aggrega statistiche
        print("Aggregating profiling data...")
        aggregated_stats = aggregate_profiling_data(profiling_runs)
        
        # Genera report markdown
        print("Generating markdown report...")
        report_content = generate_markdown_report(
            instance_idx, map_name, starts, goals,
            instance_robustness_params, aggregated_stats, 
            successful_runs, total_elapsed_times
        )
        
        # Salva report
        report_path = save_report(report_content, instance_idx, f"instance_{instance_idx}")
        print(f"✓ Report saved to: {report_path}")
    
    print(f"\n{'='*80}")
    print("Batch profiling analysis completed!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
