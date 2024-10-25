# kdl-deploy-tools
Collection of tools for CI/CD &amp; sustainability

## Static sites (static_site.py)

This command line python tool can copy a web site to your filesystem (i.e. make it static), report and correct some issues.

Requirements: python 3.10+ and linux-type environment equipped with wget.

How to copy a site to a `html` folder:

`python3 static_site.py copy -u https://dral.kdl.kcl.ac.uk`

`python3 static_site.py -h` for more info and actions.

## Down notifier (uptime.py)

This script will email a list of down sites.

`python3 uptime.py`

It is meant to run a few times a day as a cron job.

**Before running it**, create a config file under `env/uptime.py` with the following parameters:

```python
EMAIL_SERVER = 'YOUR_SMTP_DOMAIN'
EMAIL_TO=[
  'RECIPIENT_1',
  'RECIPIENT_2',
]
EMAIL_FROM = 'SENDER'
UPTIME_API_KEY = 'YOUR_UPTIME_ROBOT_READ_ONLY_API_KEY'
```
