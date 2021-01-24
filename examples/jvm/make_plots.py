import importlib
import sys
from itertools import izip

import numpy as np

import matplotlib.pyplot as plt
import mpl_toolkits.mplot3d.axes3d as axes3d
from matplotlib import cm
from scipy.optimize import curve_fit


from spearmint.utils.database.mongodb import MongoDB

from spearmint.main import get_options, parse_resources_from_config, load_jobs, remove_broken_jobs, \
    load_task_group, load_hypers

def print_dict(d, level=1):
    if isinstance(d, dict):
        if level > 1: print ""
        for k, v in d.iteritems():
            print "  " * level, k,
            print_dict(v, level=level+1)
    else:
        print d


def surface_fit(x, y, z):
    def function(data, a, b, c):
        x = data[0]
        y = data[1]
        return a * (x**b) * (y**c)
    parameters, covariance = curve_fit(function, [x, y], z)
    model_x_data = np.linspace(min(x), max(x), 30)
    model_y_data = np.linspace(min(y), max(y), 30)
    X, Y = np.meshgrid(model_x_data, model_y_data)
    Z = function(np.array([X, Y]), *parameters)
    return X, Y, Z


def main():
    """
    Usage: python make_plots.py PATH_TO_DIRECTORY

    TODO: Some aspects of this function are specific to the simple branin example
    We should clean this up so that interpretation of plots are more clear and
    so that it works in more general cases
    (e.g. if objective likelihood is binomial then values should not be
    unstandardized)
    """
    options, expt_dir = get_options()
    print "options:"
    print_dict(options)

    # reduce the grid size
    options["grid_size"] = 400

    resources = parse_resources_from_config(options)

    # Load up the chooser.
    chooser_module = importlib.import_module('spearmint.choosers.' + options['chooser'])
    chooser = chooser_module.init(options)
    print "chooser", chooser
    experiment_name     = options.get("experiment-name", 'unnamed-experiment')

    # Connect to the database
    db_address = options['database']['address']
    sys.stderr.write('Using database at %s.\n' % db_address)
    db         = MongoDB(database_address=db_address)

    # testing below here
    jobs = load_jobs(db, experiment_name)
    remove_broken_jobs(db, jobs, experiment_name, resources)

    print "resources:", resources
    print_dict(resources)
    resource = resources.itervalues().next()

    task_options = { task: options["tasks"][task] for task in resource.tasks }
    print "task_options:"
    print_dict(task_options) # {'main': {'likelihood': u'NOISELESS', 'type': 'OBJECTIVE'}}

    task_group = load_task_group(db, options, resource.tasks)
    print "task_group", task_group # TaskGroup
    print "tasks:"
    print_dict(task_group.tasks) # {'main': <spearmint.tasks.task.Task object at 0x10bf63290>}


    hypers = load_hypers(db, experiment_name)
    print "loaded hypers", hypers # from GP.to_dict()

    hypers = chooser.fit(task_group, hypers, task_options)
    print "\nfitted hypers:"
    print_dict(hypers)

    lp, x = chooser.best()
    x = x.flatten()
    print "best", lp, x
    bestp = task_group.paramify(task_group.from_unit(x))
    print "expected best position", bestp

    # get the grid of points
    grid = chooser.grid
    # print "chooser objectives:",
    # print_dict(chooser.objective)
    print "chooser models:", chooser.models
    print_dict(chooser.models)
    obj_model = chooser.models[chooser.objective['name']]
    obj_mean, obj_var = obj_model.function_over_hypers(obj_model.predict, grid)

    # un-normalize the function values and variances
    obj_task = task_group.tasks['main']
    obj_mean = [obj_task.unstandardize_mean(obj_task.unstandardize_variance(v)) for v in obj_mean]
    obj_std = [obj_task.unstandardize_variance(np.sqrt(v)) for v in obj_var]

    # for xy, m, v in izip(grid, obj_mean, obj_var):
    #     print xy, m, v

    grid = map(task_group.from_unit, grid)

    xymv = [(xy[0], xy[1], m, v, xy[2], xy[3], xy[4]) for xy, m, v in izip(grid, obj_mean, obj_std)]

    x = map(lambda x:x[0], xymv)
    y = map(lambda x:x[1], xymv)
    z = map(lambda x:x[4], xymv)
    p = map(lambda x:x[5], xymv)
    q = map(lambda x:x[6], xymv)
    m = map(lambda x:x[2], xymv)
    sig = map(lambda x:x[3], xymv)

    ## ----------------------------------------------------------------------------------------- ##
    ## ------------------------------------- PLOT FIGURES -------------------------------------- ##
    ## ----------------------------------------------------------------------------------------- ##
    fig = plt.figure(dpi=100)
    # ax = fig.add_subplot(111, projection='3d')
    ax = fig.add_subplot(111)

    ## get the observed points
    task = task_group.tasks['main']
    idata = task.valid_normalized_data_dict
    # print "idata: ", idata
    xy = idata["inputs"]
    xy = map(task_group.from_unit, xy)
    xy = np.array(xy)
    vals = idata["values"]
    vals = [obj_task.unstandardize_mean(obj_task.unstandardize_variance(v)) for v in vals]

    ## plot gc_time (vals) in terms of tests
    xaxis = list(range(1, len(vals) + 1))
    ax.scatter(xaxis, vals)
    for j in range(len(vals)):
        ax.annotate("({},{},{},{},{})".format(int(xy[j][0]),int(xy[j][1]),int(xy[j][2]),int(xy[j][3]),int(xy[j][4])), (xaxis[j], vals[j]), va='bottom', rotation=60)
    ax.set_xlabel("tests")
    ax.set_ylabel("gc_time / ms")
    ax.legend(["(G1RegionSize, GCThreads, PrefetchStyle, InstancePrefetch, PrefetchLines)"])

    ## plot errorbars
    # for i in np.arange(0, len(x)):
    #     ax.plot([x[i], x[i]], [y[i], y[i]], [m[i]+sig[i], m[i]-sig[i]], marker="_", color='k')

    ## plot means
    # ax.plot(y, z, m, marker='.', linestyle="None")

    ## plot fitted-surface of means
    # s1, s2, s3 = surface_fit(x, y, m)
    # surf = ax.plot_surface(s1, s2, s3, cmap=cm.coolwarm, linewidth=0, antialiased=False)
    # fig.colorbar(surf, shrink=0.5, aspect=5)

    ## plot (x, y, z)
    # img = ax.plot(xy[:,0], xy[:,1], vals, marker='o', color='r', linestyle="None")
    # ax.xaxis.set_ticks(np.arange(0, 4, 1))
    # ax.yaxis.set_ticks(np.arange(1, 7, 1))

    # img = ax.scatter(xy[:,0], xy[:,1], xy[:,2], c=vals,  cmap=plt.hot())
    # cbar = fig.colorbar(img)
    # cbar.set_label('gc_time in ms', rotation=90)

    ## Test-3
    # # ax.set_xlabel("G1MaxNewSizePercent: (X*10)%")
    # ax.set_xlabel("G1HeapRegionSize: exp(2,Y)/M")
    # # ax.set_ylabel("G1HeapRegionSize: exp(2,Y)/M")
    # ax.set_ylabel("ParallelGCThreads")
    # # ax.set_zlabel('ParallelGCThreads')
    # ax.set_zlabel('GC_Time')

    ## Test-4
    # ax.set_xlabel("AllocatePrefetchStyle")
    # ax.set_ylabel("AllocatePrefetchLines")
    # # ax.set_zlabel("AllocatePrefetchLines")
    # ax.set_zlabel("GC_Time")

    plt.show()


if __name__ == "__main__":
    main()
