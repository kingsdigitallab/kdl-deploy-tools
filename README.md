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


## GPUs on SLURM (hpc-gpus)

Shows number of available gpus per type on SLURM cluster at any given moment.

```bash

python hpc-gpus.py

       GPU | left (gpu) | max  (gpu) | left (int) | max  (int)
--------------------------------------------------------------
  a100_40g |          6 |         40 |          2 |         36
  a100_80g |          0 |          0 |          1 |         41
       a30 |          0 |          0 |          0 |          8
       a40 |          0 |          0 |          0 |          6
      h100 |          0 |          0 |          0 |         11
        ib |          0 |          0 |          0 |          0
      l40s |          0 |          0 |          2 |         19
   rtx2080 |          0 |          0 |          1 |          4
   rtx3070 |          0 |          0 |          9 |         10
        t4 |          0 |          0 |          0 |          6
   titan_v |          0 |          0 |          0 |          2
  titan_xp |          0 |          0 |          0 |          2
      v100 |          0 |          0 |          0 |          4
```

Where `int` stands for `interruptible_gpu` partition.

## GPU hoarder killer (kill-gpu-hoarder.py)

Kills processes that allocate significant GPU VRAM but remain idle for too long.

```bash
python3 kill-gpu-hoarder.py
```

Requirements: NVIDIA GPU, `nvidia-smi`, python 3.6+. Must be run as **root**.

Edit the constants at the top of the script to configure thresholds:

* `VRAM_THRESHOLD_GB` (default: `2`) — minimum VRAM usage to be considered
* `INACTIVE_LIMIT_MINUTES` (default: `10`) — how long a process can stay at 0% GPU compute before being killed
* `CHECK_INTERVAL_SECONDS` (default: `5`) — polling interval

## List models behind litellm API (litellmodels.py)

Before the first run set the following variables in your `env/litellmodels.py` script:
`API_URL` (API entry point), `TOKEN` (your litellm API token).

```bash
python3 litellmodels.py 

arc:apex_pro    perplexity/arc-apex_pro        moonshotai/Kimi-K2.6       262144 VISION
arc:apex        hosted_vllm/arc:apex           moonshotai/Kimi-K2.6       262144 VISION
arc:nexus       hosted_vllm/arc:nexus          Qwen/Qwen3.6-35B-A3B       262144 VISION
arc:lite        ollama_chat/arc:lite           Google/Gemma4:26b           32768 VISION
arc:nano        ollama_chat/arc:nano           Google/Gemma4:e4b            8192 VISION
arc:embed       ollama/qwen3-embedding:0.6b    qwen/qwen3-embedding-0.6b    None       
medgemma1.5:4b  ollama/medgemma1.5:4b          Google/medgemma1.5:4b       32768 VISION
```

## Analog (analog.py)

Analyse web access log files. Run `python3 analog.py --help` to see available actions.
