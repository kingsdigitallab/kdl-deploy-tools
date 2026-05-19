"""Analyse web access log files.
Authors: opencode:kimi-k2.6
Prompted & tweaked by GN
"""
import argparse
import re
from collections import Counter
from pathlib import Path

DEFAULT_LOG_PATH = 'access.log'
IP_PATTERN = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'


def run_action():
    actions = _get_actions_info()
    epilog = 'Actions:\n'
    for name, info in actions.items():
        epilog += f'  {name}:\n    {info["description"]}\n'

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
        description='Analyse web access log files.'
    )
    parser.add_argument('action', help='action to perform', choices=actions.keys())
    parser.add_argument('-f', '--file', help='path to the access log file', default=DEFAULT_LOG_PATH)
    args = parser.parse_args()

    actions[args.action]['function'](args)


def _get_actions_info():
    ret = {}
    for k, v in globals().items():
        if k.startswith('action_'):
            name = k[7:]
            description = (v.__doc__ or '').split('\n')[0]
            ret[name] = {
                'function': v,
                'description': description
            }
    return ret


def action_ip_freq(args):
    """Return the number of times each IP appears, from most to least frequent."""
    log_path = Path(args.file)
    if not log_path.exists():
        print(f'ERROR: log file not found ({log_path})')
        return

    ip_counts = Counter()
    with log_path.open('r') as f:
        for line in f:
            match = re.match(IP_PATTERN, line)
            if match:
                ip_counts[match.group(1)] += 1

    for ip, count in ip_counts.most_common():
        print(f'{count}\t{ip}')


if __name__ == '__main__':
    run_action()
