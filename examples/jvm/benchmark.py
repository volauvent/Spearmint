import numpy as np
import math
import os
import subprocess
import json
import re


def parse_exe_time(job_id):
    ## ===== DaCapo evaluation-git+309e1fa cassandra completed warmup 17 in 5567 msec =====
    path = "output/{:08d}.out".format(int(job_id))
    if not os.path.exists(path):
        print "File does not exist: " + path
        return []

    regex = re.compile(r"^===== DaCapo evaluation-git\+309e1fa (.+) completed warmup (\d+) in (\d+) msec =====$")
    file = open(path, "r")
    time_list = []
    for line in file:
        result = regex.match(line)
        if result and int(result.group(2)) >= 100:
            time_list.append(int(result.group(3)))
    return time_list

def benchmark(job_id, xms, G1MaxNewSizePercent, G1HeapRegionSize, MaxInlineLevel,
              ParallelGCThreads, AllocatePrefetchStyle, MaxGCPauseMillis):

    with open('./config.json') as f:
        data = json.load(f)

    print "Experiment config: ", data

    test_name = data["experiment-name"]
    gc_dir = test_name + "-gc"
    if not os.path.exists(gc_dir):
        os.mkdir(gc_dir)
    output_dir = "output"

    ## JVM configs
    G1MaxNewSizePercent = G1MaxNewSizePercent * 10
    G1HeapRegionSize = pow(2, int(G1HeapRegionSize))
    MaxGCPauseMillisList = [10, 50, 100, 150, 200]
    MaxGCPauseMillis = MaxGCPauseMillisList[int(MaxGCPauseMillis)]

    ## Real running time would be tests_num * iter_num
    tests_num = 2
    iter_num = 40
    benchmark_service = "cassandra"

    ## Dacapo benchmark service start cmd
    start_benchmark_cmd = lambda test_id: "sh -c " +\
        ("\"echo \$$ > /sys/fs/cgroup/cpu/myCGroupOf4Cores.slice/tasks && " + \
         "java -XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:+DisableExplicitGC -XX:+UnlockDiagnosticVMOptions -XX:+AlwaysPreTouch " + \
         "-Xms{}g -Xmx{}g " + \
         "-XX:G1MaxNewSizePercent={} " + \
         "-XX:G1HeapRegionSize={}m " + \
         "-XX:MaxInlineLevel={} " + \
         "-XX:ParallelGCThreads={} " + \
         "-XX:AllocatePrefetchStyle={} " + \
         "-XX:MaxGCPauseMillis={} " + \
         "\"-Xlog:gc*,safepoint:file={}/gc{}-{}.log:tags,uptime,time,level::filecount=1,filesize=100m\" " + \
         "-jar dacapo-evaluation-git+309e1fa.jar -n {} {}\"").format(
             int(xms), int(xms),
             int(G1MaxNewSizePercent),
             int(G1HeapRegionSize),
             int(MaxInlineLevel),
             int(ParallelGCThreads),
             int(AllocatePrefetchStyle),
             int(MaxGCPauseMillis),
             gc_dir, test_id, int(job_id),
             int(iter_num), benchmark_service)

    ## Old GC Parser
    # gc_parser_cmd = "cat %s/gc1-%s.log | grep \"ms\" | grep \"\[gc \" | awk '{print $11}' | cut -c1-5 | awk '{s+=$1} END {print s}'" % (gc_dir, job_id)

    ## New GC Parser, only calculate STW GC related time
    gc_parser_cmd = lambda test_id: "cat %s/gc%s-%s.log | grep \"ms\" | grep \"\[gc \" | grep -v \"Concurrent Cycle\" | perl -ne 'print \"$1\n\" if /(\d+\.\d+)(ms)/' | awk '{s+=$1} END {print s}'" \
        % (gc_dir, test_id, job_id)


    ## Start benchmark service
    time_list = []
    for idx in range(tests_num):
        print start_benchmark_cmd(idx)
        subprocess.call([start_benchmark_cmd(idx)], shell=True)
        print gc_parser_cmd(idx)
        time_list.append(float(subprocess.check_output([gc_parser_cmd(idx)], shell=True)))

    # print "Parsing execution time"
    # time_list = parse_exe_time(job_id)

    print "All tests time: ", time_list
    avg_val = sum(time_list) / len(time_list)
    print "Avg test time: ", float(avg_val)

    return float(avg_val)

# Write a function like this called 'main'
def main(job_id, params):
    print 'Anything printed here will end up in the output directory for job #%d' % job_id
    print "Testing: ", params
    return benchmark(job_id, params['xms'], params['G1MaxNewSizePercent'],
                     params['G1HeapRegionSize'], params['MaxInlineLevel'],
                     params['ParallelGCThreads'], params['AllocatePrefetchStyle'],
                     params['MaxGCPauseMillis'])
