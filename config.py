#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun 22 11:03:32 2018

@author: yannis
"""

indiv = []

buildings = [
             "./model/BarreMontreau.idf",
             "./model/TourMontreau.idf",
             "./model/ClotFrancais.idf",
            ]

area = {"ClotFrancais.idf" : 1990,
         "BarreMontreau.idf" : 302,
         "TourMontreau.idf" : 850}

IDF_WINDOWS = None
IDF_WALLS = None

TEMPORALITY = True # False if no sequencing nor phasing

PHASED_NOT_SEQUENCED = True # True if phased, False if sequenced, useless if TEMPORALITY = False

IDDPATH = "/usr/local/EnergyPlus-8-6-0/Energy+.idd"
EPLUSPATH = "/usr/local/EnergyPlus-8-6-0/"

NGEN = 100
IND = 96
CX = 0.8
MX = 0.2

NPARAM = 4 * len(buildings)

CONSTRAINTS = True

# Bounds walls
LOW_WALLS, UP_WALLS = 0, 40
# Bounds windows
LOW_WINDOW, UP_WINDOW = 0, 4
BOUNDS = [(LOW_WALLS, UP_WALLS), (LOW_WALLS, UP_WALLS),
          (LOW_WALLS, UP_WALLS), (LOW_WINDOW, UP_WINDOW)] * len(buildings)


# Bounds phasing
if TEMPORALITY:
    BOUNDS += [(0, len(BOUNDS) - 1) for i in range(len(BOUNDS))]
    NDIM = 2 * NPARAM
else:
    NDIM = NPARAM

# buildings = [
#              "./model/BarreMontreau.idf",
#              "./model/TourMontreau.idf",
#             ]

BUDGET = [55000,
          55000,
          110000,
          55000]
#Global : 275k€, 1750€/


lock = None
