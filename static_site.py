'''
Display the URLs that wget couldn't successfully request (40x, 500).
Write redirect pages where wget copied the redirected content.
'''
import argparse
from pathlib import Path
import re

SERVER_PORT = '8000'
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
        err_path=LOG_FILENAME
    )

def _error(message):
    print(f'ERROR: {message}')
    exit(1)

def action_report(parser):
    '''Report errors found during last copy.'''
    errors, redirects = _parse_copy_log()

    for code, issues in errors.items():
        for url in sorted(list(issues.keys())):
            print(f'{code}\t{url}')

    for r_from, r_to in redirects.items():
        print(f'->\t{r_from}\t{r_to}')

    root_url = _read_root_url()

    for p in Path(COPY_PATH).glob('**/*.html'):
        content = p.read_text()
        if re.search(r'\bindex\.html\b', content):
            print(f'"index.html" in {p}')
        if root_url in content:
            print(f'domain "{root_url}" hard-coded in {p}')
        if re.search(r'<link\b[^>]+\bhref="http', content):
            print(f'external <link> in {p}')
            

def action_redirect(parser):
    '''Write redirect pages under 'html'.'''
    errors, redirects = _parse_copy_log()

    root_url = _read_root_url()
    for r_from, r_to in redirects.items():
        print(f'->\t{r_from}\t{r_to}')

        r_from = re.sub(r'^([^#?]+).*$', r'\1', r_from)
        path = Path(r_from.replace(root_url, COPY_PATH + '/')) / 'index.html'
        if path.exists():
            content = re.sub(r'\{\{\s*REDIRECT_URL\s*\}\}', r_to, REDIRECT_TEMPLATE)
            path.write_text(content)
        else:
            print(f'WARNING: "{path}" not found')

def action_relink(parser):
    '''Improve hyperlinks. Remove /index.html and domain from internal links.'''
    base_url = _read_root_url()
    for p in Path(COPY_PATH).glob('**/*.html'):
        content = p.read_text()
        content_new = re.sub(
            r'(\s(?:src|href)\s*=\s*")([^"#?]+)',
            lambda m: _relink(m, base_url),
            content
        )
        if content_new != content:
            p.write_text(content_new)
            print(f'UPDATED {str(p)}')

def _relink(match, base_url):
    '''Remove /index.html and domain from internal links
    e.g. href="https//mysite.com/a/b/index.html?q=1" 
    => href="/a/b/?q=1" 
    '''
    url = match.group(2)
    # remove hard-coded domain to make the copy more portable
    url = url.replace(base_url, '/')
    # remove /index.html if url is internal
    if not url.startswith('http'):
        url = url.replace('index.html', '')
    ret = match.group(1) + url
    return ret

def _read_root_url():
    '''Returns the first URL found at the end of line in the log file'''
    ret = None
    with open(LOG_FILENAME, 'r') as f:
        for line in f:
            part = line.strip().split()[-1]
            if part.startswith('http'):
                ret = part
                break
    if ret is None:
        _error('Could not extract the root URL from the copy log.')

    return ret

def action_serve(parser):
    '''Locally serves the copy of the site'''
    _run_command('python3', '-m', 'http.server', '-d', 'html', SERVER_PORT)

def _parse_copy_log():
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

def _run_command(*args, out_path=None, err_path=None):
    import subprocess

    stdout_file = open(out_path, "w") if out_path else None
    stderr_file = open(err_path, "w") if err_path else None
    
    ret = subprocess.run(
        args,
        stdout=stdout_file,
        stderr=stderr_file
    )

    if stdout_file:
        stdout_file.close()
    if stderr_file:
        stderr_file.close()


    return ret

if __name__ == '__main__':
    run_action()
