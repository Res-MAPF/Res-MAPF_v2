import time
from collections import defaultdict
from contextlib import contextmanager

class GranularProfiler:
    """
    Granular profiler to track time and number of calls of specific functions.
    Supports both inclusive (nested) and exclusive time tracking.
    """
    
    def __init__(self):
        self.metrics = defaultdict(lambda: {
            'calls': 0,
            'total_time': 0.0,      # Inclusive time (including children)
            'exclusive_time': 0.0,  # Exclusive time (excluding children)
            'child_time': 0.0,      # Total time spent in direct children
            'min_time': float('inf'),
            'max_time': 0.0,
        })
        self.call_stack = []
        self.enabled = True
        self.counters = defaultdict(int)

    def increment_counter(self, name, amount=1):
        """Increment a named integer counter (e.g. number of CBS conflicts)"""
        self.counters[name] += amount

    @contextmanager
    def measure(self, function_name):
        """Context manager to measure time and count calls"""
        if not self.enabled:
            yield
            return
        
        start_time = time.perf_counter()
        parent_name = self.call_stack[-1] if self.call_stack else None
        
        self.call_stack.append(function_name)
        
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start_time
            self.call_stack.pop()
            
            metric = self.metrics[function_name]
            metric['calls'] += 1
            metric['total_time'] += elapsed
            metric['exclusive_time'] += elapsed  # Will be corrected when children complete
            metric['min_time'] = min(metric['min_time'], elapsed)
            metric['max_time'] = max(metric['max_time'], elapsed)
            
            # Track child time in parent
            if parent_name:
                parent_metric = self.metrics[parent_name]
                parent_metric['child_time'] += elapsed
    
    def get_stats(self, func_name=None):
        """Get statistics for a specific function or all"""
        if func_name:
            if func_name not in self.metrics:
                return None
            metric = self.metrics[func_name]
            return {
                'name': func_name,
                'ncalls': metric['calls'],
                'cumtime': metric['total_time'],
                'tottime': metric['total_time'],
                'mean_time': metric['total_time'] / metric['calls'] if metric['calls'] > 0 else 0,
                'min_time': metric['min_time'] if metric['min_time'] != float('inf') else 0,
                'max_time': metric['max_time'],
            }
        else:
            return {
                func: self.get_stats(func)
                for func in self.metrics.keys()
            }
    
    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.call_stack.clear()
        self.counters.clear()
    
    def generate_report(self):
        """Generate a detailed bottleneck report"""
        report = []
        report.append("\n" + "="*80)
        report.append("GRANULAR PROFILING REPORT")
        report.append("="*80)
        
        # Sort by total time
        sorted_metrics = sorted(
            self.metrics.items(),
            key=lambda x: x[1]['total_time'],
            reverse=True
        )
        
        total_time = sum(m[1]['total_time'] for m in sorted_metrics)
        
        report.append(f"\nTotal measured time: {total_time:.4f}s\n")
        report.append(f"{'Function':<40} {'Calls':>8} {'Total(s)':>12} {'Avg(ms)':>12} {'Min(ms)':>12} {'Max(ms)':>12} {'%Time':>8}")
        report.append("-"*100)
        
        for func_name, metric in sorted_metrics:
            calls = metric['calls']
            total = metric['total_time']
            avg = total / calls if calls > 0 else 0
            min_t = metric['min_time'] if metric['min_time'] != float('inf') else 0
            max_t = metric['max_time']
            pct = (total / total_time * 100) if total_time > 0 else 0
            
            report.append(
                f"{func_name:<40} {calls:>8} {total:>12.4f} {avg*1000:>12.2f} "
                f"{min_t*1000:>12.2f} {max_t*1000:>12.2f} {pct:>7.1f}%"
            )
        
        report.append("\n" + "="*80)
        report.append("BOTTLENECK ANALYSIS")
        report.append("="*80)
        
        # Identify bottlenecks
        if sorted_metrics:
            top_func = sorted_metrics[0]
            report.append(f"\nTop bottleneck: {top_func[0]}")
            report.append(f"  - Time: {top_func[1]['total_time']:.4f}s ({top_func[1]['total_time']/total_time*100:.1f}%)")
            report.append(f"  - Calls: {top_func[1]['calls']}")
            report.append(f"  - Avg time per call: {top_func[1]['total_time']/top_func[1]['calls']*1000:.2f}ms")
        
        return "\n".join(report)
    
    def print_report(self):
        """Print the report"""
        print(self.generate_report())
    
    def get_report_dict(self):
        """Return statistics as a dictionary for CSV/analysis"""
        stats = {}

        # Aggregate entries with _agent_X suffixes (e.g., low_level_search_cbs_agent_0, _agent_1, etc.)
        aggregated_metrics = defaultdict(lambda: {
            'calls': 0,
            'total_time': 0.0,
            'exclusive_time': 0.0,
            'child_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
        })

        for func_name, metric in self.metrics.items():
            # Check if this is an agent-specific metric (e.g., low_level_search_cbs_agent_0)
            if '_agent_' in func_name:
                # Extract base name (e.g., low_level_search_cbs from low_level_search_cbs_agent_0)
                base_name = func_name.split('_agent_')[0]
                aggregated_metrics[base_name]['calls'] += metric['calls']
                aggregated_metrics[base_name]['total_time'] += metric['total_time']
                aggregated_metrics[base_name]['exclusive_time'] += metric['exclusive_time']
                aggregated_metrics[base_name]['child_time'] += metric['child_time']
                aggregated_metrics[base_name]['min_time'] = min(aggregated_metrics[base_name]['min_time'], metric['min_time'])
                aggregated_metrics[base_name]['max_time'] = max(aggregated_metrics[base_name]['max_time'], metric['max_time'])
            else:
                # Non-agent metrics are kept as-is
                aggregated_metrics[func_name] = metric
        
        # Convert to output format - calculate corrected exclusive time
        for func_name, metric in aggregated_metrics.items():
            # Exclusive time = total time - child time
            total_t = metric['total_time']
            child_t = metric['child_time']
            excl_t = max(0, total_t - child_t)  # Ensure non-negative
            
            stats[func_name] = {
                'ncalls': metric['calls'],
                'cumtime': round(total_t, 4),
                'exclusive_time': round(excl_t, 4),
                'child_time': round(child_t, 4),
                'mean_time': round(total_t / metric['calls'], 5) if metric['calls'] > 0 else 0,
                'mean_exclusive': round(excl_t / metric['calls'], 5) if metric['calls'] > 0 else 0,
                'min_time': round(metric['min_time'] if metric['min_time'] != float('inf') else 0, 5),
                'max_time': round(metric['max_time'], 5),
            }
        return stats


# Global profiler instance
_global_profiler = GranularProfiler()


def get_profiler():
    """Return the global profiler instance"""
    return _global_profiler


@contextmanager
def profile_section(section_name):
    """Global context manager for code sections"""
    with _global_profiler.measure(section_name):
        yield
