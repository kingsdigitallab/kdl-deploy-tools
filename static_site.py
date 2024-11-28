'''
Display the URLs that wget couldn't successfully request (40x, 500).
Write redirect pages where wget copied the redirected content.
'''
import argparse
from pathlib import Path
import urllib.parse
import re

SERVER_PORT = '8010'
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
        description='Create and maintain a copy of a site.'
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
        # This looks buggy.
        # 1. it convert #x into index.html#x
        # 2. or r/index.html#x if r is a redirect!
        # '--convert-links',
        '--adjust-extension',
        '--page-requisites',
        '--no-parent',
        '-P', COPY_PATH, 
        '-nH', parser.url,
        err_path=LOG_FILENAME
    )

def action_copy_and_fix(parser):
    '''Run all actions. Copy a site then fix the copy.'''
    action_copy(parser)
    action_dedupe(parser)
    action_redirect(parser)
    action_relink(parser)
    action_rename(parser)
    action_report(parser)

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
    root_domain = _get_domain_from_url(root_url)

    unique_external_links = set()

    paths = []
    for pattern in ['**/*.html', '**/*.css']:
        paths.extend(Path(COPY_PATH).glob(pattern))

    for p in paths:
        if '?' in str(p):
            print(f'? in file name {p}')

        content = p.read_text()

        # get all urls ending in index.html
        index_urls = re.findall(r'''[/\w.:-]*\bindex\.html\b''', content)
        # keep only the internal ones
        index_urls = [
            url 
            for url in index_urls
            if _get_domain_from_url(url) in ['', root_domain]
        ]
        if index_urls:
            print(f'index.html found {len(index_urls)} in {p}')
        if root_domain in content:
            print(f'domain "{root_domain}" hard-coded in {p}')
        absolute_paths = re.findall(r'(src|href|action)\s*=\s*"/[^/]', content)
        if absolute_paths:
            print(f'{len(absolute_paths)} absolute paths found in @src, @href or @action. {p}')

        # in css
        absolute_paths = re.findall(r'\burl\(\s*"/[^/]', content)
        if absolute_paths:
            print(f'{len(absolute_paths)} absolute paths found in url(). {p}')
        
        external_links = set(re.findall(r'<link\b[^>]+\bhref\s*=\s*"(http[^"]+)', content))
        new_external_links = external_links.difference(unique_external_links)
        if new_external_links:
            # print(external_links)
            # if re.search(r'<link\b[^>]+\bhref\s*=\s*"(http[^"]+)', content):
            print(f'{len(new_external_links)} new external <link> in {p}')
            unique_external_links = unique_external_links.union(new_external_links)

def action_dedupe(parser):
    '''Removes a.html if same as a/index.html. Remove query strings from file names '?'.'''
    for p in Path(COPY_PATH).glob('**/*.html'):
        # content = p.read_text()
        if p.name != 'index.html':
            # case 1, a/index.html
            p2 = p.parent / p.stem / 'index.html'

            # case 2, ? in file name
            if '?' in str(p.name):
                # e.g. html/photos/index.html?phrase=.html
                p2 = p.parent / re.sub(r'\?.*$', '', p.name)

            # (re)move
            if p2.exists():
                if p.read_text() == p2.read_text():
                    print(f'REMOVED {p}, SAME AS {p2}')
                    p.unlink()
                else:
                    print(f'WARNING: {p} <> {p2}')
            else:
                print(f'MOVED {p} to {p2}')
                p.replace(p2)
                
def action_redirect(parser):
    '''Write redirect pages under 'html'.'''
    errors, redirects = _parse_copy_log()

    root_url = _read_root_url()
    for r_from, r_to in redirects.items():
        print(f'->\t{r_from}\t{r_to}')

        r_from = re.sub(r'^([^#?]+).*$', r'\1', r_from)
        path = Path(r_from.replace(root_url, COPY_PATH + '/')) / 'index.html'
        found = path.exists()
        if not found:
            # try decoding the URL
            path_decoded = Path(urllib.parse.unquote(str(path)))
            if path_decoded != path:
                path = path_decoded
                found = path.exists() 
        
        if not found:
            print(f'WARNING: "{path}" not found')
        else:
            depth = len(path.relative_to(COPY_PATH).parents) - 1
            r_to = _relink_url(r_to, root_url, depth)
            content = re.sub(r'\{\{\s*REDIRECT_URL\s*\}\}', r_to, REDIRECT_TEMPLATE)
            ## path.write_text(content)

def action_relink(parser):
    '''Improve hyperlinks. Remove /index.html & domain from internal links. Make paths relative.'''
    base_url = _read_root_url()

    paths = []
    for pattern in ['**/*.html', '**/*.css']:
        paths.extend(Path(COPY_PATH).glob(pattern))

    for p in paths:
        depth = len(p.relative_to(COPY_PATH).parents) - 1
        content = p.read_text()
        pattern = r'(\s(?:src|href|action|poster|srcset)\s*=\s*")([^"#?]+)'
        if str(p).endswith('.css'):
            pattern = r'(url\(")([^"#?]+)'
        content_new = re.sub(
            pattern,
            lambda m: _relink_urls(m, base_url, depth),
            content
        )
        if content_new != content:
            p.write_text(content_new)
            print(f'UPDATED {str(p)}')

def _relink_urls(match, base_url, depth):
    # srcset="url1 w h, url2 w h, ..."
    ret = ','.join([
        _relink_url(url, base_url, depth)
        for url 
        in re.split(r',\s*', match.group(2))
    ])
    
    return match.group(1) + ret

def _relink_url(part, base_url, depth):
    '''Remove /index.html and domain from internal links
    e.g. href="https//mysite.com/a/b/index.html?q=1" 
    => href="/a/b/?q=1" 
    '''
    ret = part
    # remove hard-coded domain to make the copy more portable
    ret = ret.replace(base_url, '/')

    if not _get_domain_from_url(ret):
        # remove /index.html if url is internal
        ret = ret.replace('index.html', '')
        # convert absolute paths to relative (so site can be hosted on github)
        # e.g. /x/y/z => ../x/y/z
        if ret.startswith('/'):
            ret = '../' * depth + ret[1:]

    return ret

def action_rename(parser):
    '''Remove ?... from file names (e.g. x.css?v=5.6.1).'''
    for p in Path(COPY_PATH).glob('**/*'):
        p_new = re.sub(r'\?[^/]*$', '', str(p))
        if p_new != str(p):
            print(f'rename {p} into {p_new}')
            p.rename(p_new)

def _get_domain_from_url(url):
    # return '' if domain is not present in <url>
    return urllib.parse.urlparse(url).netloc

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

def action_tag(parser):
    '''Tag content for PageFind utility'''
    # TODO: generalise. At the moment h2 is specific to renskin project.
    for p in Path(COPY_PATH).glob('**/*.html'):
        content = p.read_text()
        content_new = re.sub(
            r'data-pagefind-\w+(="[^"]*")?',
            '',
            content,
        )
        if 1:
            content_new = re.sub(
                r'<h2\s*',
                '<h2 data-pagefind-weight="10.0" data-pagefind-meta="title"',
                content_new,
                count=1
            )
            content_new = re.sub(
                r'nav"\s*>',
                'nav" data-pagefind-ignore>',
                content_new,
            )
        if content_new != content:
            p.write_text(content_new)
            print(f'UPDATED {str(p)}')


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
