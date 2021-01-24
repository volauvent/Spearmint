import numpy as np
import math
import os
import subprocess
import json


def benchmark(job_id, x, y, z, p, q):

    with open('./config.json') as f:
        data = json.load(f)

    print "Experiment config: ", data

    test_name = data["experiment-name"]
    gc_dir = test_name + "-gc"
    if not os.path.exists(gc_dir):
        os.mkdir(gc_dir)


    ## ---------------- test-3 ------------------ ##
    # x = x * 10
    # y = pow(2,int (y))

    # start_benchmark_cmd = "sh -c " +\
    #     "\"echo \$$ > /sys/fs/cgroup/cpu/myCGroupOf4Cores.slice/tasks && java -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:+DisableExplicitGC -XX:+UnlockDiagnosticVMOptions -XX:+AlwaysPreTouch -Xms16g -Xmx16g -XX:G1MaxNewSizePercent={} -XX:G1HeapRegionSize={}m -XX:ParallelGCThreads={} \"-Xlog:gc*,safepoint:file={}/gc-{}.log:tags,uptime,time,level::filecount=1,filesize=100m\" -jar dacapo-evaluation-git+309e1fa.jar -n 100 lusearch\"".format(int(x), int(y), int(z), gc_dir, int(job_id))
    # subprocess.call([start_benchmark_cmd], shell=True)


    ## ---------------- test-4 and test-5 and test 6------------------ ##
    ## Test 4 in the doc
    # start_benchmark_cmd = "sh -c " +\
    #     "\"echo \$$ > /sys/fs/cgroup/cpu/myCGroupOf4Cores.slice/tasks && java -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:+DisableExplicitGC -XX:+UnlockDiagnosticVMOptions -XX:+AlwaysPreTouch -Xms16g -Xmx16g -XX:G1MaxNewSizePercent=80 -XX:G1HeapRegionSize=32m -XX:ParallelGCThreads=5 -XX:AllocatePrefetchStyle={} -XX:AllocateInstancePrefetchLines={} -XX:AllocatePrefetchLines={} \"-Xlog:gc*,safepoint:file={}/gc-{}.log:tags,uptime,time,level::filecount=1,filesize=100m\" -jar dacapo-evaluation-git+309e1fa.jar -n 500 lusearch\"".format(int(x), int(y), int(z), gc_dir, int(job_id))
    # subprocess.call([start_benchmark_cmd], shell=True)


    ## ----------------- test-7 ------------------- ##
    ## Test 5 in the doc
    x = pow(2, int(x))
    start_benchmark_cmd = "sh -c " +\
        "\"echo \$$ > /sys/fs/cgroup/cpu/myCGroupOf4Cores.slice/tasks && java -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:+DisableExplicitGC -XX:+UnlockDiagnosticVMOptions -XX:+AlwaysPreTouch -Xms16g -Xmx16g -XX:G1MaxNewSizePercent=80 -XX:G1HeapRegionSize={}m -XX:ParallelGCThreads={} -XX:AllocatePrefetchStyle={} -XX:AllocateInstancePrefetchLines={} -XX:AllocatePrefetchLines={} \"-Xlog:gc*,safepoint:file={}/gc-{}.log:tags,uptime,time,level::filecount=1,filesize=100m\" -jar dacapo-evaluation-git+309e1fa.jar -n 200 lusearch\"".format(int(x), int(y), int(z), int(p), int(q), gc_dir, int(job_id))
    subprocess.call([start_benchmark_cmd], shell=True)


    ## Collect gc result
    gc_time = 0
    gc_parser_cmd = "cat %s/gc-%s.log | grep \"ms\" | grep \"\[gc \" | awk '{print $11}' | cut -c1-5 | awk '{s+=$1} END {print s}'" % (gc_dir, job_id)
    gc_time = subprocess.check_output([gc_parser_cmd], shell=True)
    print "GC time result: ", float(gc_time)

    return float(gc_time)

# Write a function like this called 'main'
def main(job_id, params):
    print 'Anything printed here will end up in the output directory for job #%d' % job_id
    print "Testing: ", params
    return benchmark(job_id, params['x'], params['y'], params['z'], params['p'], params['q'])
