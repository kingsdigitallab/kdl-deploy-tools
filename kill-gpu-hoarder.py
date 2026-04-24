'''
This script kills any process that hoards VRAM on a GPU 
while keeping it idle for a long time.

It should be run as root.

It was written by Brave AI with following prompt:

"a python script that kills processes which have more than x GB of allocated VRAM on local GPU but haven't done any compute on the GPU for y minutes"
'''

import subprocess
import time
import os
import signal
from datetime import datetime

# --- CONFIGURATION ---
VRAM_THRESHOLD_GB = 2  # Kill if process uses more than this many GB
INACTIVE_LIMIT_MINUTES = 10  # Kill if 0% compute for this long
# CHECK_INTERVAL_SECONDS = 60  # How often to check
CHECK_INTERVAL_SECONDS = 5  # How often to check

# Tracker: {pid: last_active_timestamp}
idle_tracker = {}

def log(message):
    """Prints a message with a current timestamp prefix."""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {message}")

def get_gpu_stats():
    """Returns a dict of {pid: {'mem_gb': float, 'util': int}}"""
    stats = {}
    try:
        # Get memory usage: pid, used_gpu_memory (MiB)
        mem_raw = subprocess.check_output(
            ['nvidia-smi', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'],
            encoding='utf-8'
        ).strip()
        
        for line in mem_raw.split('\n'):
            if not line: continue
            pid, mem_mib = map(int, line.split(','))
            stats[pid] = {'mem_gb': mem_mib / 1024, 'util': 0}

        # Get utilization: Use 'pmon' to see per-process %sm (Streaming Multiprocessor) usage
        pmon_raw = subprocess.check_output(
            ['nvidia-smi', 'pmon', '-c', '1', '-s', 'u'],
            encoding='utf-8'
        ).strip().split('\n')
        
        # skip headers
        for line in pmon_raw[2:]:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    pid = int(parts[1])
                    sm_util = int(parts[3].replace('-', '0')) # '-' means 0 or unknown
                    if pid in stats:
                        stats[pid]['util'] = sm_util
                except ValueError:
                    continue
    except Exception as e:
        log(f"Error reading GPU stats: {e}")
    return stats

def main():
    log(f"Monitoring GPU for processes > {VRAM_THRESHOLD_GB}GB VRAM and idle for > {INACTIVE_LIMIT_MINUTES}min...")
    
    while True:
        current_stats = get_gpu_stats()
        now = time.time()
        
        # Clean up tracker for processes that finished on their own
        tracked_pids = list(idle_tracker.keys())
        for pid in tracked_pids:
            if pid not in current_stats:
                del idle_tracker[pid]

        for pid, data in current_stats.items():
            is_heavy = data['mem_gb'] > VRAM_THRESHOLD_GB
            is_idle = data['util'] == 0
           
            if is_heavy and is_idle:
                if pid not in idle_tracker:
                    idle_tracker[pid] = now
                    log(f"[TRACKING] PID {pid} is heavy ({data['mem_gb']:.2f}GB) and idle.")
                else:
                    idle_time_min = (now - idle_tracker[pid]) / 60
                    if idle_time_min >= INACTIVE_LIMIT_MINUTES:
                        log(f"[KILL] PID {pid} idle for {idle_time_min:.1f}min. Terminating...")
                        try:
                            os.kill(pid, signal.SIGTERM)
                            del idle_tracker[pid]
                        except ProcessLookupError:
                            pass
            else:
                # Process is either light or currently working
                if pid in idle_tracker:
                    log(f"[RESET] PID {pid} is active (util {data['util']}%) or freed memory.")
                    del idle_tracker[pid]

        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
