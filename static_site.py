'''
Display the URLs that wget couldn't successfully request (40x, 500).
Write redirect pages where wget copied the redirected content.
'''
import argparse
from pathlib import Path
import re

COPY_PATH = 'html'
LOG_FILENAME = 'copy.log'
REDIRECT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Refresh" content="0; url='{{REDIRECT_URL}}'">
<title></title>
</head>
<body>
</body>
</html>
'''


def run_action():
    actions = {}
    epilog = 'Action:\n'

    actions = _get_actions_info()
    for name, info in actions.items():
        epilog += f'  {name}:\n    {info['description']}\n'

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )
    
    parser.add_argument("action", help="action to perform", choices=actions.keys())
    parser.add_argument("-u", "--url", help="root url of site to copy")
    args = parser.parse_args()

    actions[args.action]['function'](args)
    
    print(f'done ({args.action})')

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

def action_copy(parser):
    '''Copy a website into files under a 'html' folder.'''
    # 'https://renaissanceskin.ac.uk/'
    if not parser.url:
        _error('pass a valid URL to the copy action using -u')
    if Path(COPY_PATH).exists():
        _error(f'output folder already exists ({COPY_PATH})')

    res = _run_command(
        'wget',
        '--mirror',
        '--convert-links', 
        '--adjust-extension',
        '--page-requisites', 
        '--no-parent', 
        '-P', COPY_PATH, 
        '-nH', parser.url,
        out_path='copy_out.log', 
        err_path=LOG_FILENAME
    )
    print(res)

def _error(message):
    print(f'ERROR: {message}')
    exit(1)

def action_report(parser):
    '''Report errors found during last copy.'''
    errors, redirects = _parse_wget_log()

    for code, issues in errors.items():
        for url in sorted(list(issues.keys())):
            print(f'{code}\t{url}')

    for r_from, r_to in redirects.items():
        print(f'->\t{r_from}\t{r_to}')

def action_redirect(parser):
    '''Write redirect pages under 'html'.'''
    errors, redirects = _parse_wget_log()

    for r_from, r_to in redirects.items():
        print(f'->\t{r_from}\t{r_to}')

        path = Path(re.sub(r'^https?://([^#]+)', r'\1', r_from)) / 'index.html'
        if path.exists():
            content = re.sub(r'\{\{\s*REDIRECT_URL\s*\}\}', r_to, REDIRECT_TEMPLATE)
            path.write_text(content)

def action_noindex(parser):
    '''Remove /index.html from all hyperlinks.'''
    from pathlib import Path
    for p in Path(COPY_PATH).glob('**/*.html'):
        content = p.read_text()
        content_new = re.sub(r'(href\s*=\s*"[^"]*/)index\.html\b', r'\1', content)
        if content_new != content:
            p.write_text(content_new)

def _run_command(*args, out_path='stdout.log', err_path='stderr.log'):
    import subprocess

    with open(out_path, "w") as stdout_file, open(err_path, "w") as stderr_file:
        process = subprocess.run(
            args,
            stdout=stdout_file,
            stderr=stderr_file
        )

def _parse_wget_log():
    '''Parses stderr from GNU Wget 1.21.4.'''
    errors = {}
    redirects = {}

    content = Path(LOG_FILENAME).read_text()
    for line in content.split('\n'):
        locations = re.findall(r'^Location: ([^\s]+) ', line)
        if locations:
            location = locations[0]
            redirects[url] = location
        urls = re.findall(r'\s(http[^\s]+)$', line)
        if urls:
            url = urls[0]
        codes = re.findall(r'\sERROR (\d+):', line)
        if codes:
            code = codes[0]
            if code not in errors:
                errors[code] = {}
            errors[code][url] = 1
    
    return errors, redirects

if __name__ == '__main__':
    run_action()
