# kdl-deploy-tools
Collection of small tools for CI/CD &amp; sustainability

## Static sites (static_site.py)

This command line python tool can copy a web site to your filesystem (i.e. make
it static), report and correct some issues.

Requirements: python 3.10+ and linux-type environment equipped with wget.

How to copy a site to a `html` folder:

`python3 static_site.py copy -u https://dral.kdl.kcl.ac.uk`

`python3 static_site.py -h` for more info and actions.

## Down notifier (uptime.py)

This script will email a list of down sites.

`python3 uptime.py`

It is meant to run a few times a day as a cron job.

Requirements: python 3.5+

**Before running it**, create a config file under `env/uptime.py` with the
following parameters:

```python
EMAIL_SERVER = 'YOUR_SMTP_DOMAIN'
EMAIL_TO=[
  'RECIPIENT_1',
  'RECIPIENT_2',
]
EMAIL_FROM = 'SENDER'
UPTIME_API_KEY = 'YOUR_UPTIME_ROBOT_READ_ONLY_API_KEY'
```

## Mercurial to Git converter ([hg2git.sh](hg2git.sh))

This script converts a Mercurial repository to a Git repository and preserves
the commit history.

`./hg2git.sh /path/to/mercurial/repository`

For more information, see the script itself.

## Visual Regression Toolkit (vireg)

This tool is used for visual regression testing. It compares two images and
reports any differences.

More info in the [README.md file](vireg/README.md).
