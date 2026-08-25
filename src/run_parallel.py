"""
Parallel driver for a run_cli.py-style JSON config: fans instances out across
a multiprocessing.Pool via a dynamic work queue (Pool.imap_unordered), since
per-instance runtime is too skewed for a static N-way split to load-balance
well. Each worker writes its own CSV (build_solutions_csv has no file
locking for concurrent writers); merge_results.py concatenates them after.

    python -m src.run_parallel --file src/batch_all.json --set-name v3_sweep \\
        --workers 22 --out-dir results_parts/v3

Also works in a v2 worktree if it has a run_cli_v2.py with the same
run_one_instance signature (imported as a fallback below). Do not run a v2
batch and a v3 batch concurrently on the same machine -- CPU contention would
bias the elapsed_time comparison between them; run one to completion, then
the other. Parallelizing within one version's batch is fine and encouraged.
"""
import argparse
import json
import os
import time
import traceback

from tqdm import tqdm

# Imported lazily inside the worker so RESULTS_CSV_PATH is set in each
# worker's environment before sperimental_analysis reads it, and so this
# module stays cheap to import from the main process.


def _init_worker(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    os.environ["RESULTS_CSV_PATH"] = os.path.join(out_dir, f"results_worker_{os.getpid()}.csv")


def _run_one(entry_and_idx):
    idx, entry, set_name = entry_and_idx
    # The run_cli/run_cli_v2 import fallback is inside this try/except too, so
    # a missing run_cli_v2.py in the v2 worktree costs one error row instead
    # of crashing the whole pool on the first instance.
    try:
        from src.domain.MAPFInstance import RobustnessParams
        from src.utils.sperimental_analysis import build_solutions_csv
        try:
            from src.run_cli import run_one_instance, DEFAULT_TIME_LIMIT
        except ImportError:
            # v2 worktree: run_cli.py doesn't exist there -- fall back to
            # run_cli_v2.py's own run_one_instance (same signature).
            from src.run_cli_v2 import run_one_instance, DEFAULT_TIME_LIMIT

        map_name = entry["map"]
        starts = [tuple(s) for s in entry["starts"]]
        goals = [tuple(g) for g in entry["goals"]]
        k, m, h = entry["k"], entry["m"], entry["h"]
        failure_types = entry["failure_types"]
        time_limit = entry.get("time_limit", DEFAULT_TIME_LIMIT)
        granular = entry.get("granular_profiling", False)

        sol, stat, timed_out = run_one_instance(
            map_name, starts, goals, k, m, h, failure_types,
            time_limit=time_limit, granular=granular,
            instance_label=set_name, instance_idx=idx,
        )
    except Exception as e:
        from src.domain.MAPFInstance import RobustnessParams
        from src.utils.sperimental_analysis import build_solutions_csv
        from src.domain.solver.Solution import Solution
        map_name, starts, goals = entry["map"], entry["starts"], entry["goals"]
        k, m, h, failure_types = entry["k"], entry["m"], entry["h"], entry["failure_types"]
        traceback.print_exc()
        sol = Solution(None, set(), set(), dict(), dict())
        stat = {"error": f"{type(e).__name__}: {e}"}
        timed_out = False

    robustness_params = RobustnessParams(k, m, h, failure_types)
    build_solutions_csv(
        [(map_name, starts, goals)], robustness_params, [sol], set_name, [stat], [timed_out]
    )

    success = bool(sol.tau_states) if not timed_out else False
    return idx, success, timed_out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--file", required=True, help="Path to the JSON config (from generate_batch.py).")
    parser.add_argument("--set-name", required=True, help="test_case_name tag, e.g. v3_sweep_small.")
    parser.add_argument("--out-dir", required=True, help="Directory to write per-worker results_worker_<pid>.csv files into.")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 2),
                         help="Worker processes. Default: cpu_count - 2 (leaves headroom for the OS). "
                              "Default: %(default)s")
    args = parser.parse_args()

    with open(args.file, encoding="utf-8") as f:
        config = json.load(f)

    print(f"{len(config)} instances, {args.workers} workers, writing per-worker CSVs to {args.out_dir}/")
    start = time.perf_counter()

    import multiprocessing as mp
    successes, timeouts, errors = 0, 0, 0
    with mp.Pool(processes=args.workers, initializer=_init_worker, initargs=(args.out_dir,)) as pool:
        tasks = [(i, entry, args.set_name) for i, entry in enumerate(config)]
        with tqdm(total=len(tasks), desc=args.set_name, unit="instance") as pbar:
            for idx, success, timed_out in pool.imap_unordered(_run_one, tasks):
                if timed_out:
                    timeouts += 1
                elif success:
                    successes += 1
                else:
                    errors += 1
                pbar.set_postfix(solved=successes, timeout=timeouts, other=errors)
                pbar.update(1)

    elapsed = time.perf_counter() - start
    print(f"\n*** '{args.set_name}' completed: {successes}/{len(config)} solved, "
          f"{timeouts} timeouts, {errors} other, in {elapsed/3600:.2f}h wall-clock "
          f"({args.workers} parallel workers).")
    print(f"Per-worker CSVs are in {args.out_dir}/ -- merge with src.merge_results once "
          f"this version's other batch(es) are also done.")


if __name__ == "__main__":
    main()
