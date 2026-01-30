import subprocess
import re
import json

'''
NodeName=erc-hpc-vm013 Arch=x86_64 CoresPerSocket=6 
   CPUAlloc=1 CPUEfctv=10 CPUTot=12 CPULoad=0.92
   AvailableFeatures=icelake,a100,a100_80g
   ActiveFeatures=icelake,a100,a100_80g
   Gres=gpu:1(S:0-1)
   NodeAddr=erc-hpc-vm013 NodeHostName=erc-hpc-vm013 Version=23.11.5
   OS=Linux 6.8.0-59-generic #61~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Tue Apr 15 17:03:15 UTC 2 
   RealMemory=117000 AllocMem=0 FreeMem=106487 Sockets=2 Boards=1
   CoreSpecCount=2 CPUSpecList=5,11 MemSpecLimit=10240
   State=MIXED ThreadsPerCore=1 TmpDisk=0 Weight=1 Owner=N/A MCS_label=N/A
   Partitions=gpu 
   BootTime=2025-05-15T23:02:37 SlurmdStartTime=2025-05-27T14:47:44
   LastBusyTime=2025-06-05T21:22:14 ResumeAfterTime=None
   CfgTRES=cpu=10,mem=117000M,billing=10,gres/gpu=1
   AllocTRES=cpu=1,gres/gpu=1
   CapWatts=n/a
   CurrentWatts=0 AveWatts=0
   ExtSensorsJoules=n/a ExtSensorsWatts=0 ExtSensorsTemp=n/a
'''


res = subprocess.run(["scontrol","show", "nodes", "--json"], capture_output=True, text=True)
# print(res.stdout)

scontrol_output = json.loads(res.stdout)

def find(pattern, str, default=''):
   ret = default

   matches = re.findall(pattern, str)
   if matches:
      ret = matches[0]
   
   return ret

# sort nodes by gpu then partition
# then count the number of available & used gpu per group

partitions = set()

stats = {

}
for node in scontrol_output['nodes']:
   if len(node['active_features']) > 1:
      gpu = node['active_features'][-1]
      if gpu == 'ib' and len(node['active_features']) > 2:
         gpu = node['active_features'][-2]

      name = node['name']
      partition = node['partitions'][0]
      
      if gpu not in stats:
         stats[gpu] = {}
      if partition not in stats[gpu]:
         stats[gpu][partition] = {
            'count': 0,
            'used': 0,
            'left': 0,
            'used_nodes': [],
            'left_nodes': [],
         }
      
      partitions.add(partition)

      # "tres": "cpu=124,mem=755000M,billing=124,gres\/gpu=3",
      # "tres_used": "cpu=6,gres\/gpu=3",

      tres = node['tres']
      tres_used = node['tres_used']
      gpu_count = int(find(r'gres/gpu=(\d+)', node['tres'], 0))
      gpu_used = int(find(r'gres/gpu=(\d+)', node['tres_used'], 0))
      stats[gpu][partition]['count'] += gpu_count
      stats[gpu][partition]['used'] += gpu_used
      stats[gpu][partition]['left'] += gpu_count - gpu_used
      if gpu_used:
         stats[gpu][partition]['used_nodes'].append(name)
      else:
         stats[gpu][partition]['left_nodes'].append(name)

FILTER = 'a100_80g'
FILTER = ''

if 0:
   if FILTER:
      print(json.dumps(stats[FILTER], indent=2))
   else:
      print(json.dumps(stats, indent=2))

# display results in a table

partitions = sorted([p for p in list(partitions) if p != 'cpu'])

header = ['GPU']
for partition in partitions:
   header.append(f'left ({partition[:3]})')
   header.append(f'max  ({partition[:3]})')

row = ' | '.join([f'{c:>10}' for c in header])
print(row)

print('-' * len(row))

for gpu_key in sorted(stats):
   info = stats[gpu_key]
   cells = [
      gpu_key
   ]
   for partition in partitions:
      part_info = info.get(partition, {'count': 0, 'used': 0, 'left': 0})
      cells += [part_info['left'], part_info['count']]

   row = ' | '.join([f'{c:>10}' if c else ' ' * 10 for c in cells])

   print(row)

