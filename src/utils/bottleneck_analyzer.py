"""
Bottleneck Analyzer: Analizza i dati di profiling per identificare bottleneck in ResPlaN.
Fornisce report dettagliati sulla distribuzione del tempo e sul numero di operazioni.
"""

from src.utils.granular_profiler import get_profiler
import json


class BottleneckAnalyzer:
    """
    Analizza i risultati del profiling granulare per identificare bottleneck
    e fornire raccomandazioni di ottimizzazione.
    """
    
    def __init__(self):
        self.profiler = get_profiler()
    
    def analyze(self):
        """Esegue l'analisi completa dei bottleneck"""
        stats = self.profiler.get_stats()
        
        if not stats:
            return {
                'total_time': 0,
                'components': {},
                'bottlenecks': [],
                'recommendations': []
            }
        
        # Categorizza i risultati per componente
        components_breakdown = self._categorize_by_component(stats)
        
        # Calcola i bottleneck
        bottlenecks = self._identify_bottlenecks(stats, components_breakdown)
        
        # Genera raccomandazioni
        recommendations = self._generate_recommendations(bottlenecks, components_breakdown)
        
        return {
            'total_time': sum(s['cumtime'] for s in stats.values() if s),
            'components': components_breakdown,
            'bottlenecks': bottlenecks,
            'recommendations': recommendations,
            'raw_stats': stats
        }
    
    def _categorize_by_component(self, stats):
        """Categorize results by main component"""
        categories = {
            'ResPlaN': {
                'time': 0,
                'calls': 0,
                'functions': []
            },
            'CBS': {
                'time': 0,
                'calls': 0,
                'functions': []
            },
            'SIPPS': {
                'time': 0,
                'calls': 0,
                'functions': []
            }
        }
        
        for func_name, stat in stats.items():
            if stat is None:
                continue
                
            time = stat.get('cumtime', 0)
            calls = stat.get('ncalls', 0)
            
            if 'CBS' in func_name or 'heuristic_computation' in func_name or 'build_solution' in func_name or 'detect_conflict' in func_name or 'compute_plan_cbs' in func_name:
                categories['CBS']['time'] += time
                categories['CBS']['calls'] += calls
                categories['CBS']['functions'].append((func_name, time, calls))
            elif 'resplan_iteration' in func_name or 'resplan' in func_name.lower() or 'rcheck' in func_name or 'process_macroaction' in func_name or 'compute_affected_actions' in func_name or 'pop_and_check_signature_in_sets' in func_name or 'macroaction_loop' in func_name or 'extract_solution_from_predecessors' in func_name:
                categories['ResPlaN']['time'] += time
                categories['ResPlaN']['calls'] += calls
                categories['ResPlaN']['functions'].append((func_name, time, calls))
            elif 'SIPPS' in func_name or 'low_level' in func_name or 'build_safe' in func_name:
                categories['SIPPS']['time'] += time
                categories['SIPPS']['calls'] += calls
                categories['SIPPS']['functions'].append((func_name, time, calls))
            else:
                # Qualsiasi altra funzione va in ResPlaN
                categories['ResPlaN']['time'] += time
                categories['ResPlaN']['calls'] += calls
                categories['ResPlaN']['functions'].append((func_name, time, calls))
        
        return categories
    
    def _identify_bottlenecks(self, stats, components):
        """Identify main bottlenecks"""
        bottlenecks = []
        
        # Find total times per component
        total_time = sum(c['time'] for c in components.values())
        
        if total_time == 0:
            return bottlenecks
        
        for component_name, component_data in components.items():
            comp_time = component_data['time']
            comp_percentage = (comp_time / total_time) * 100 if total_time > 0 else 0
            
            bottleneck = {
                'component': component_name,
                'time': comp_time,
                'percentage': comp_percentage,
                'calls': component_data['calls'],
                'avg_time_per_call': comp_time / component_data['calls'] if component_data['calls'] > 0 else 0,
                'functions': sorted(
                    component_data['functions'],
                    key=lambda x: x[1],
                    reverse=True
                )[:5]  # Top 5 functions
            }
            bottlenecks.append(bottleneck)
        
        # Sort by decreasing time
        bottlenecks.sort(key=lambda x: x['time'], reverse=True)
        
        return bottlenecks
    
    def _generate_recommendations(self, bottlenecks, components):
        """Generate optimization recommendations"""
        recommendations = []
        
        if not bottlenecks:
            return recommendations
        
        # Check the most expensive component
        top_bottleneck = bottlenecks[0]
        
        if top_bottleneck['percentage'] > 50:
            recommendations.append({
                'priority': 'HIGH',
                'message': f"{top_bottleneck['component']} occupies {top_bottleneck['percentage']:.1f}% of total time (it's the 80/20 of the problem)",
                'suggestion': f"Concentrate optimization on {top_bottleneck['component']}"
            })
        
        # Analyze number of calls vs time
        for bottleneck in bottlenecks:
            calls = bottleneck['calls']
            avg_time = bottleneck['avg_time_per_call']
            
            if calls > 1000 and avg_time < 0.001:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'message': f"{bottleneck['component']}: High number of calls ({calls}) but low average time ({avg_time*1000:.3f}ms)",
                    'suggestion': "The problem might be in call overhead. Consider memoization or batch processing."
                })
            
            if avg_time > 0.1 and calls > 10:
                recommendations.append({
                    'priority': 'HIGH',
                    'message': f"{bottleneck['component']}: High average time per call ({avg_time*1000:.1f}ms) with {calls} calls",
                    'suggestion': "Each single call is expensive. Try to optimize the internal algorithm."
                })
        
        # Compare SIPPS vs CBS
        sipps_time = components.get('SIPPS', {}).get('time', 0)
        cbs_time = components.get('CBS', {}).get('time', 0)
        
        if cbs_time > sipps_time * 2:
            recommendations.append({
                'priority': 'HIGH',
                'message': f"CBS is {cbs_time/sipps_time:.1f}x more expensive than SIPPS",
                'suggestion': "The problem is likely in CBS search space expansion. Check the number of detected conflicts."
            })
        
        if sipps_time > cbs_time * 2:
            recommendations.append({
                'priority': 'MEDIUM',
                'message': f"SIPPS is {sipps_time/cbs_time:.1f}x more expensive than CBS",
                'suggestion': "Each low-level search is expensive. Check the complexity of safe interval table construction."
            })
        
        return recommendations
    
    def print_analysis(self):
        """Print formatted analysis"""
        analysis = self.analyze()
        
        print("\n" + "="*80)
        print("BOTTLENECK ANALYSIS - ResPlaN PROFILING")
        print("="*80)
        
        print(f"\nTOTAL EXECUTION TIME: {analysis['total_time']:.4f}s\n")
        
        print("COMPONENT BREAKDOWN:")
        print("-" * 80)
        print(f"{'Component':<20} {'Time(s)':>12} {'Calls':>12} {'Avg/Call(ms)':>15} {'%':>8}")
        print("-" * 80)
        
        for bottleneck in analysis['bottlenecks']:
            component = bottleneck['component']
            time = bottleneck['time']
            calls = bottleneck['calls']
            avg = bottleneck['avg_time_per_call']
            pct = bottleneck['percentage']
            
            print(f"{component:<20} {time:>12.4f} {calls:>12} {avg*1000:>15.2f} {pct:>7.1f}%")
        
        print("\n" + "="*80)
        print("TOP BOTTLENECKS")
        print("="*80)
        
        for i, bottleneck in enumerate(analysis['bottlenecks'][:3], 1):
            print(f"\n{i}. {bottleneck['component']}")
            print(f"   Time: {bottleneck['time']:.4f}s ({bottleneck['percentage']:.1f}%)")
            print(f"   Calls: {bottleneck['calls']}")
            print(f"   Avg/Call: {bottleneck['avg_time_per_call']*1000:.2f}ms")
            
            if bottleneck['functions']:
                print(f"   Top Functions:")
                for func, func_time, func_calls in bottleneck['functions']:
                    print(f"     - {func}: {func_time:.4f}s ({func_calls} calls)")
        
        print("\n" + "="*80)
        print("RECOMMENDATIONS")
        print("="*80)
        
        if analysis['recommendations']:
            for rec in analysis['recommendations']:
                priority = rec['priority']
                message = rec['message']
                suggestion = rec['suggestion']
                
                print(f"\n[{priority}]")
                print(f"  Issue: {message}")
                print(f"  Action: {suggestion}")
        else:
            print("\nNo specific recommendations at this time.")
        
        print("\n" + "="*80 + "\n")
    
    def get_report_dict(self):
        """Return analysis as dictionary"""
        return self.analyze()
    
    def export_to_json(self, filename):
        """Export analysis to JSON format"""
        analysis = self.analyze()
        
        # Convert numpy types if necessary
        def convert_to_serializable(obj):
            if isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_serializable(v) for v in obj]
            elif isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            else:
                return str(obj)
        
        with open(filename, 'w') as f:
            json.dump(convert_to_serializable(analysis), f, indent=2)
        
        print(f"\nAnalysis exported to {filename}")


def analyze_bottlenecks():
    """Convenience function to analyze bottlenecks"""
    analyzer = BottleneckAnalyzer()
    analyzer.print_analysis()
    return analyzer.get_report_dict()
