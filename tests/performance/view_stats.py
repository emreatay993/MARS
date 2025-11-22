import pstats
import sys
import os

def view_stats(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        return

    try:
        p = pstats.Stats(file_path)
        p.strip_dirs().sort_stats('cumulative').print_stats(20)
    except Exception as e:
        print(f"Error reading stats file: {e}")

if __name__ == "__main__":
    stats_file = 'tests/performance/output/solver_profile.stats'
    if len(sys.argv) > 1:
        stats_file = sys.argv[1]
    
    print(f"Viewing stats from: {stats_file}")
    view_stats(stats_file)
