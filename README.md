# kdl-deploy-tools
Collection of tools for CI/CD &amp; sustainability

## Static sites

This command line python tool can copy a web site to your filesystem (i.e. make it static), report and correct some issues.

Requirements: python 3.10+ and linux-type environment equipped with wget.

How to copy a site to a `html` folder:

`python3 static_site.py copy -u https://dral.kdl.kcl.ac.uk`

`python3 static_site.py -h` for more info and actions.

