## Using spearmint to auto-tune Dacapo JVM services performance
=========================================

### Setting up

**STEP 1: Setup spearmint**
1. Create a Python2 virtual env and follow intructions in README in the project root to setup spearmint engine

**STEP 2: Create a CGroup**

Create a CGroup to setup a consistent running evn. All steps below need to be performed with root access. So please login as root using `sudo su`

1. Change directory to /sys/fs/cgroup/ and execute all subsequent steps from that directory: `cd /sys/fs/cgroup/`
2. Create a folder with a CGroup name of your choice: `mkdir cpu/myCGroupOf4Cores.slice`
3. Set CFS Scheduler period to 100ms: `echo 100000 >  cpu/myCGroupOf4Cores.slice/cpu.cfs_period_us`
4. Set CFS Scheduler quota of your CGroup - as a multiple of CFS Period. The “multiple” here should be the number of cores you want to assign to your CGroup: `echo 400000 >  cpu/myCGroupOf4Cores.slice/cpu.cfs_quota_us`

**STEP 3: Running spearmint with sudo**
1. Start up a MongoDB daemon instance:
`mongod --fork --logpath <path/to/logfile\> --dbpath <path/to/dbfolder\>`
2. Run spearmint: `sudo env "PATH=$PATH" python ./spearmint/main.py ./examples/jvm/ |& tee -a output.txt`
