"""
Detailed profiling stats viewer for solver_profile.stats
"""
import pstats
import sys
from pstats import SortKey

def view_stats_detailed(file_path):
    """View profiling statistics in multiple sorted views"""
    
    print("=" * 80)
    print(f"PROFILING RESULTS: {file_path}")
    print("=" * 80)
    
    # Load stats
    stats = pstats.Stats(file_path)
    stats.strip_dirs()
    
    # View 1: Top 30 by cumulative time
    print("\n" + "=" * 80)
    print("TOP 30 FUNCTIONS BY CUMULATIVE TIME")
    print("=" * 80)
    stats.sort_stats(SortKey.CUMULATIVE)
    stats.print_stats(30)
    
    # View 2: Top 30 by total time (self time)
    print("\n" + "=" * 80)
    print("TOP 30 FUNCTIONS BY TOTAL TIME (SELF TIME)")
    print("=" * 80)
    stats.sort_stats(SortKey.TIME)
    stats.print_stats(30)
    
    # View 3: Callers of top functions
    print("\n" + "=" * 80)
    print("CALLERS OF TOP 10 FUNCTIONS")
    print("=" * 80)
    stats.sort_stats(SortKey.CUMULATIVE)
    stats.print_callers(10)
    
    # View 4: What top functions call
    print("\n" + "=" * 80)
    print("CALLEES OF TOP 10 FUNCTIONS")
    print("=" * 80)
    stats.sort_stats(SortKey.CUMULATIVE)
    stats.print_callees(10)

if __name__ == "__main__":
    stats_file = r'C:\Users\emre_\PycharmProjects\MARS_\tests\performance\output\solver_profile.stats'
    if len(sys.argv) > 1:
        stats_file = sys.argv[1]
    
    view_stats_detailed(stats_file)
