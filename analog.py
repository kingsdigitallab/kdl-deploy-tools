"""Analyse web access log files.
Authors: opencode:kimi-k2.6
Prompted & tweaked by GN

114.119.163.186 - - [19/May/2026:00:00:54 +0000] "GET /digipal/page/5504/?graph=13741 HTTP/1.1" 200 25251 "https://www.modelsofauthority.ac.uk/digipal/page/5504?graph=13813" "Mozilla/5.0 (Linux; Android 7.0;) AppleWebKit/537.36 (HTML, like Gecko) Mobile Safari/537.36 (compatible; PetalBot;+https://webmaster.petalsearch.com/site/petalbot)"
"""
import argparse
import re
from collections import Counter
from pathlib import Path

DEFAULT_LOG_PATH = 'access.log'
IP_PATTERN = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
AGENT_PATTERN = r'"([^"]*)"\s*$'


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


def _validate_log_path(path_str):
    ret = Path(path_str)
    if not ret.exists():
        print(f'ERROR: log file not found ({ret})')
        return None
    return ret


def _count_pattern(log_path, pattern, group=1):
    ret = Counter()
    with log_path.open('r') as f:
        for line in f:
            match = re.search(pattern, line)
            if match:
                ret[match.group(group)] += 1
    return ret


def _print_counts(counts):
    for item, count in counts.most_common():
        print(f'{count}\t{item}')


def action_ip_freq(args):
    """Return the number of times each IP appears, from most to least frequent."""
    log_path = _validate_log_path(args.file)
    if not log_path:
        return

    counts = _count_pattern(log_path, IP_PATTERN)
    _print_counts(counts)


def action_agent_freq(args):
    """Return the number of times each user agent appears, from most to least frequent."""
    log_path = _validate_log_path(args.file)
    if not log_path:
        return

    counts = _count_pattern(log_path, AGENT_PATTERN)
    _print_counts(counts)


if __name__ == '__main__':
    run_action()
