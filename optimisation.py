#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import random
import datetime
import multiprocessing
from multiprocessing import Lock
import logging
import logging.handlers
import numpy as np
import pandas as pd

from deap import base
from deap import creator
from deap import tools

import config
from evaluationEP import evaluation


import logzero
from logzero import logger
logzero.loglevel(logging.DEBUG)
logzero.logfile("./activity.log", maxBytes=2e6, backupCount=30)
logger.propagate = False

#     Problem definition
NPARAM = config.NPARAM
NDIM = config.NDIM

BOUNDS = config.BOUNDS

toolbox = base.Toolbox()


def init_indp(icls, ranges, genome=list()):
    """
    Initialization of individuals: this function initializes with integer the
    individuals with respect to the bounds given in input and phasing

    Args:
        icls (creator): class created for Individuals
        ranges (list): Bounds for individuals

    Returns:
        icls (creator): Individuals created initialized with random genome

    """
    genome = list()
    if genome == list():
        logger.debug(ranges)
        if config.TEMPORALITY:
            nparam = len(ranges) // 2

            for p in ranges[0:nparam]:
                genome.append(np.random.randint(*p))

            genome += random.sample(range(nparam), nparam)
        else:
            nparam = len(ranges)

            for p in ranges[0:nparam]:
                genome.append(np.random.randint(*p))

    return icls(genome)


def init_auto(icls, pcls, ranges):
    """
    ToDo: Docstring
    """
    try:
        genome = init_file() 
        return pcls(icls(ind) for ind in genome)

    except IOError:
        pop = init_ind(icls, ranges)
        return pop


def init_file():
    """
    ToDo: Docstring
    """
    with open("monitoring.csv", "r") as data:
        content = data.read()
    content = content.split("\n")
    monit = []
    line = []

    from ast import literal_eval
    for row in content[1:-1]:
        line = []
        row = literal_eval(row)
        line.append(literal_eval(row[1]))
        line.append(literal_eval(row[2]))
        monit.append(line)

    ind = []
    for gen in monit[-config.IND:]:
        ind.append(gen[1])
    return ind


def init_population(n):
    try:
        monit = init_file() 
        logger.debug("monitoring indiv: %s" % (monit))
        pop = []
        for item in monit:
            pop.append(toolbox.individual(genome=item))
        logger.debug("pop from monit: %s" % (pop))

    except IOError:
        logger.debug("New population")
        pop = toolbox.population(n=n)
    return pop


def init_ind(icls, ranges):
    """
    Initialization of individuals: this function initializes with integer the
    individuals with respect to the bounds given in input

    Args:
        icls (creator): class created for Individuals
        ranges (list): Bounds for individuals

    Returns:
        icls (creator): Individuals created initialized with random genome

    """

    genome = list()
    nparam = len(ranges) // 2

    for p in ranges[0:nparam]:
        genome.append(np.random.randint(*p))

    genome += random.sample(range(nparam), nparam)

    return icls(genome)


def init_opti():
    """
    creation of the toolboxes objects that defines
    - the type of population and the creator of individuals
    - the difference (or ot) in the initialization of individuals
    - the evaluation function
    - the crossing operator
    - the mutation operator
    - the algorithm used to select best individuals

    Args:
        None

    """
    # Creation des objects liés à l'optimisation
    creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0, -1.0))
    creator.create("Individual",
                   list,
                   typecode="d",
                   fitness=creator.FitnessMin)

    # toolbox.register("attr_int", random.randint, BOUND_LOW, UP_WALLS)
    toolbox.register("individual", init_indp, icls=creator.Individual,
                     ranges=BOUNDS)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    toolbox.register("evaluate", evaluation)
    toolbox.register("mate", tools.cxOnePoint)
    toolbox.register("matep", tools.cxUniformPartialyMatched, indpb=0)
    toolbox.register("mutate", tools.mutUniformInt, low=[x[0] for x in BOUNDS],
                     up=[x[1] for x in BOUNDS], indpb=1 / NPARAM)
    toolbox.register("mutatep", tools.mutShuffleIndexes, indpb=1 / NPARAM)

    toolbox.register("select", tools.selNSGA2)


def crossover(ind1, ind2):
    """
    Integrate a crossover that respects phasing
    """
    if config.TEMPORALITY:
        order1, order2 = ind1[len(ind1) // 2:len(ind1)
                            ], ind2[len(ind2) // 2:len(ind2)]
        ope1, ope2 = ind1[0:len(ind1) // 2], ind2[0:len(ind2) // 2]

        toolbox.mate(ope1, ope2)
        toolbox.matep(order1, order2)

        ind1[:] = ope1 + order1
        ind2[:] = ope2 + order2
    else:
        toolbox.mate(ind1, ind2)

    return ind1, ind2


def mutation(ind):
    """
    Mutation that respect phasing
    """
    logger.debug("mutation start")
    if config.TEMPORALITY:
        ope, order = ind[0:len(ind) // 2], ind[len(ind) // 2:len(ind)]

        toolbox.mutate(ope)
        toolbox.mutatep(order)

        ind[:] = ope + order
        logger.debug("mutation finished")
    else:
        toolbox.mutate(ind)

    return ind


def parameters(GEN=config.NGEN, NBIND=config.IND, CX=config.CX, MX=config.MX):
    """
    Parameters definition for a genetic algorithm. That can apply to most of
    evolutionary optimization algorithm.

    Args:
        GEN (int): Number of generation of GA
        NBIND (int): Number of Individual of GA
        CX (float): crossing probability for each individual
    """
    logger.info("NGEN: " + str(GEN) + ", Individuals: " + str(NBIND))

    return GEN, NBIND, CX, MX


def main():
    """
    Everything else to launch the optimization.

    ToDo:
        Refactor the stat modules
        Refactor the selection process in a function

    """
    NGEN, MU, CXPB, MXPB = parameters()

    pareto = tools.ParetoFront()

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", np.mean, axis=0)
    stats.register("std", np.std, axis=0)
    stats.register("min", np.min, axis=0)
    stats.register("max", np.max, axis=0)

    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"

    pop = init_population(n=MU)
    graph = []
    data = []

    logger.debug(pop)

    logger.debug("Evaluate the individuals with an invalid fitness")
    invalid_ind = [ind for ind in pop if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    logger.debug("Evaluation finished")

    data.append([ind.fitness.values for ind in pop])

    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit
        graph.append(ind.fitness.values)

    # This is just to assign the crowding distance to the individuals
    # no actual selection is done
    pop = toolbox.select(pop, len(pop))

    record = stats.compile(pop)
    logbook.record(gen=0, evals=len(invalid_ind), **record)
    logger.info(logbook.stream)

    logger.debug("Begin the generational process")
    for gen in range(1, NGEN):
        logger.debug("Generation " + str(gen) + " out of " + str(NGEN))
        logger.debug("Vary the population")
        offspring = tools.selTournamentDCD(pop, len(pop))
        offspring = [toolbox.clone(ind) for ind in offspring]

        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            if random.random() <= CXPB:
                ind1, ind2 = crossover(ind1, ind2)
                # toolbox.mate(ind1, ind2)

            ind1 = mutation(ind1)
            ind2 = mutation(ind2)
                # toolbox.mutate(ind1)
                # toolbox.mutate(ind2)

            del ind1.fitness.values, ind2.fitness.values

        logger.debug(pop)

        logger.debug("Evaluate the individuals with an invalid fitness")
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        logger.debug("Evaluation finished")

        data.extend([ind.fitness.values for ind in pop])
        config.indiv.extend([ind for ind in pop])

        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit
            graph.append(ind.fitness.values)

        # Select the next generation population
        pop = toolbox.select(pop + offspring, MU)
        record = stats.compile(pop)
        logbook.record(gen=gen, evals=len(invalid_ind), **record)
        logger.info(logbook)

        pareto.update(pop)

        monitoring(pareto, pop, gen)


    return pop, logbook, pareto, graph, data


def monitoring(pareto, currentPop, gen):
    """
    Plots the hypervolume of the population to monitor the optimization

    Args:
        pareto (pareto): contains population of Pareto front
        df: population

    Returns:

    """
    logger.debug("monitoring function")
    try:
        # try importing the C version
        from deap.tools._hypervolume import hv
    except ImportError:
        # fallback on python version
        from deap.tools._hypervolume import pyhv as hv

    # Must use wvalues * -1 since hypervolume use implicit minimization
    # And minimization in deap use max on -obj
    wobj = np.array([ind.fitness.wvalues for ind in pareto]) * -1
    ref = np.max(wobj, axis=0) * 1.5

    df = []
    df.append(hv.hypervolume(wobj, ref))

    logger.debug("calculation of HV done")

    try:
        import matplotlib.pyplot as plt
        plt.ioff()
        xaxis = [i for i in range(len(df))]
        plt.scatter(xaxis, df, c="b", marker="v")
        plt.ylabel("Hypervolume de la population")
        plt.xlabel("Génération")
        plt.title("Convergence de l\"optimisation")
        plt.savefig("monitoring_hypervolume.png")

        logger.debug("plot done")
    except Exception as e:
        logger.error("Monitoring plot error")
        logger.exception(e)

    # Dump population into csv file
    monit = pd.DataFrame([dict(vals=pop, fitness=pop.fitness.values)
                          for pop in currentPop])
    with open("monitoring.csv", "a") as f:
        monit.to_csv(f, header=False)
    logger.debug("population saved")

    # Dump pareto into csv file
    with open("pareto_monitoring.csv", "a") as f:
        f.write("generation "+str(gen)+"\n")
        np.savetxt(f, wobj, delimiter=",")
    logger.debug("pareto saved")


def write_pareto(pareto, everyindiv, data):
    """
    Write pareto front in txt file to enable further exploitation

    Args:
        pareto (pareto): pareto object from DEAP containing best individuals

    Returns:
        pareto.items (list) : list of fitnesses of pareto individuals
    """

    logger.debug("writing results in files")
    with open("./results/pareto" + str(datetime.datetime.now()) + ".txt", "w") as front:
        for line in pareto.items:
            front.write(str(line) + "\n")

    with open("./results/data" + str(datetime.datetime.now()) + ".txt", "w") as front:
        for ind in data:
            front.write(str(ind) + "\n")

    with open("./results/pareto_fitnesses" + str(datetime.datetime.now()) + ".txt", "w") as resultats:
        for ind in pareto:
            resultats.write(str(ind.fitness) + "\n")

    with open("./results/graph_data" + str(datetime.datetime.now()) + ".txt", "w") as every:
        for ind in everyindiv:
            every.write(str(ind) + "\n")

    return pareto.items


def plots(population, optimal_indiv, data):
    """
    Plots the summary of optimization
    Saves all plots in files

    Args:
        all the data provided by DEAP optimization

    Returns:
        None

    """

    logger.debug("plotting")
    import matplotlib.pyplot as plt

    front = np.array([ind.fitness.values for ind in population])
    optimal_indiv = np.array(optimal_indiv)

    plt.scatter(optimal_indiv[:, 0], optimal_indiv[:, 1],
                c="c", alpha=0.7, marker="+")
    plt.scatter(front[:, 0], front[:, 1], c="m", alpha=0.5, marker="+")
    plt.axis("tight")
    plt.ylabel("Inconfort de l\"occupant \n(°C.h en dehors de 18-28°C)")
    plt.xlabel("Consommation énergétique (kWh)")
    plt.title("Front de Pareto (en rouge) et \n individus optimaux (en bleu)")
    plt.savefig("front.png")

    x, y = zip(*data)
    c = np.array([i // 96 for i in range(len(x))])
    plt.ylabel("Inconfort de l\"occupant \n(°C.h en dehors de 18-28°C)")
    plt.xlabel("Consommation énergétique (kWh)")
    plt.title("Individus par génération")
    plt.scatter(x, y, c=c)
    plt.savefig("front2.png")

if __name__ == "__main__":
    lock = Lock()
    logger.debug("initializing")
    init_opti()


    #   Multiprocessing pool
#    pool = multiprocessing.Pool()
#    toolbox.register("map", pool.map)

    logger.debug("optimizing")
    indiv, statslog, optimal_front, graph_data, allindiv = main()
    logger.debug("out of main")


#    except Exception as e:
#        import pdb; pdb.set_trace()
#        logger.error(e)


    logger.info("Exiting program")
    indivpareto = write_pareto(optimal_front, graph_data, allindiv)
