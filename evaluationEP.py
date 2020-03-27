#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 17:44:21 2018

@author: yannis

"""
import numpy as np
import logging
import logging.handlers

from eppy import modeleditor
from eppy.modeleditor import IDF
import energyplus_wrapper as ep

import config
import fitnessesEP

import logzero
from logzero import logger
from logzero import setup_logger

log_format = '%(message)s'
monitfmt = logzero.LogFormatter(fmt=log_format)

monitoringlog = setup_logger(logfile="monitoring.log", 
                             level=logging.INFO, 
                             formatter=monitfmt)
logzero.loglevel(logging.DEBUG)



IDDPATH = config.IDDPATH
EPLUSPATH = config.EPLUSPATH

IDFPATH = "./model/"
LIBFILE = "./model/material.idf"
LIBWINDOW = "./model/windows.idf"

EPWFILE = IDFPATH + "Paris_Orly.epw"


def phasing(budget, ind):
    """
    Reorganize the phasing with respect to economy
    """
    indb = [ind[i:i + 4] for i in range(0, len(ind) // 2, 4)]
    indp = ind[len(ind) // 2:len(ind)]
    logger.debug("reorganizing sequencing into phasing")

    price_phasing = fitnessesEP.price_per_phase(indb)

    ind_phasing = [None] * len(indp)
    for phase in budget:
        price_phase = 0
        for seq in range(len(indp)):
            # Looking for sequenced already put in phasing
            if ind_phasing[indp.index(seq)] is not None:
                continue

            price_phase += price_phasing[indp.index(seq)]
            if price_phase < phase:
                ind_phasing[indp.index(seq)] = budget.index(phase)
            else:
                price_phase -= price_phasing[indp.index(seq)]
                budget[budget.index(phase) + 1] += phase - price_phase
                break
    logger.debug("phasing is %s" % (ind_phasing))
    return ind_phasing


def evaluate_phasing(ind):
    """
    Evaluate an individual with regards to the phasing chromosome. The function
    check for duplicates

    Args:
        ind (list): individual from the optimization

    Returns:
        fitnesses (tuple): results of all of the evaluations (energy need,
        comfort factor, price)
    """
    # ind = unconstrain(ind)
    budget = config.BUDGET

    inds = [0] * (len(ind) // 2)
    fitnesses = np.zeros(3)
    fitness = []
    monitoringlog.info("random message")
    try:
        index = config.indiv.index(ind)
        fitnesses = config.indiv[index].fitness.values
        logger.debug("not simulated")

        return fitnesses
    # Reorganize phasing

    except ValueError:
        # Do the phasing
        if config.PHASED_NOT_SEQUENCED:
            indp = phasing(budget, ind)
        else:
            indp = ind[len(ind) // 2:len(ind)]

        # Simulate with phasing
        works = ind[len(ind) // 2:len(ind)]
        for i in range(len(works)):

            # Find all the tasks indexes associated to this phase
            task = [j for j in range(len(works)) if indp[j] == i]
            logger.debug("task for phase %s : %s" % (i, task))
          
            if len(task) is 0 and i is not 0:
                logger.info("phase %s same phase as previous" % (i))
                fitnesses = fitnesses + fitness
                logger.debug("fitnesses = %s" % (fitnesses))
                continue

            for j in task:
                inds[j] = ind[j]
            logger.debug("ind phasing: %s" % (inds))

            fitness = fitnessesEP.evaluate(inds)

            fitnesses = fitnesses + fitness
            logger.debug("fitnesses = %s" % (fitnesses))

        # On 20 years:
        logger.debug("Adding %s years of fitness" % (20-max(works)))
        fitnesses += fitness * (20-max(works))
        monitoringlog.info((ind, indp, fitnesses.tolist()))
        return fitnesses


def feasible(ind):
    """Feasibility function for the individual. Returns True if feasible False
    otherwise."""

    incomp = [[10, 3],[10, 4],[20, 3],[20, 4],[30, 3],[30, 4],[40, 3],
              [40, 4],[1, 4],[4, 4],[21, 4],[31, 4],[8, 0],[18, 0],[28, 0],
              [38, 0],[9, 0],[9, 1],[19, 0],[19, 1],[29, 0],[29, 1],[39, 0],
              [39, 1]]

    if [ind[0], ind[3]] in incomp:
        return False
    elif[ind[4], ind[7]] in incomp:
        return False
    elif[ind[8], ind[11]] in incomp:
        return False
    return True


def evaluation(ind):
    if config.TEMPORALITY:
        fitness = evaluate_phasing(ind)
    else:
        fitness = fitnessesEP.evaluate(ind)
    
    if config.CONSTRAINTS:
        if not feasible(ind):
            return fitness*2
    
    return fitness
    
    

if __name__ == "__main__":
    import random
    indiv = ((random.sample(range(27), 3) + random.sample(range(5), 1)) * 3
             + random.sample(range(12), 12))
    logger.debug(indiv)
    output = evaluate_phasing(indiv)
    logger.info(output)
