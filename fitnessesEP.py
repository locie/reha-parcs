#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

@author: yannis

"""
import pandas as pd
import numpy as np
import logging
import logging.handlers
import ast
import time

from eppy import modeleditor
from eppy.modeleditor import IDF
import energyplus_wrapper as ep
import config

import logzero
from logzero import logger
from logzero import setup_logger

log_format = '%(message)s'
monitfmt = logzero.LogFormatter(fmt=log_format)

monitbuilding = setup_logger(logfile="monitbuilding.log", 
                             level=logging.INFO, 
                             formatter=monitfmt)

logzero.loglevel(logging.DEBUG)
log = logging.getLogger()
log.addHandler(logging.StreamHandler())
logzero.logger.addHandler(log)
# logger.propagate = False

IDDPATH = config.IDDPATH
EPLUSPATH = config.EPLUSPATH

IDFPATH = "./model/"
LIBFILE = "./model/material.idf"
LIBWINDOW = "./model/windows.idf"

EPWFILE = IDFPATH + "Paris_Orly.epw"


def initialize(idf):
    """
    Creation of Eppy IDF object for one building

    args:
        idf (str): path to the idf file

    returns:
        model (IDF): Eppy building model

    """
    logger.debug("Eppy initialization")
    IDF.setiddname(IDDPATH)
    model = IDF(idf, EPWFILE)

    return model


def build_library(model, libfile, libwindow, epwfile):
    """
    Loading of Material and building Construction in the optimized IDF.

    args:
        model (IDF) : future optimized IDF
        libfile (str) : path to IDF containing materials to add to model
        epwfile (EPW) : any EPW file, not used for simulation but needed to
                        load libfile
    returns:
        None

    Example:
        >>> IDF.setiddname(/usr/local/EnergyPlus-8-6-0/Energy+.idd)
        >>> model = IDF("./tests/test_model", "./tests/test_weather.epw")
        >>> build_library(model, "./model/test_mat.idf", "./tests/test_weather.epw")

    """
    config.IDF_WALLS = IDF(libfile, epwfile)
    logger.debug("building library with " + libfile)
    for material in config.IDF_WALLS.idfobjects["MATERIAL"]:
        config.IDF_WALLS.newidfobject("CONSTRUCTION",
                                      Name="wall_" + str(material.Name),
                                      Outside_Layer=material.Name,
                                      Layer_2="Plancher")

    config.IDF_WINDOWS = IDF(libwindow, EPWFILE)
    for glazing in config.IDF_WINDOWS.idfobjects["WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"]:
        config.IDF_WINDOWS.newidfobject(
            "CONSTRUCTION", Name="window_" + str(glazing.Name), Outside_Layer=glazing.Name)


def modify(ind, model):
    """
    Launch modifications for classes in EP Model and

    args:
        ind (list): individual of the optimization associated with this
                    building

    returns:
        model (Eppy IDF): modified building model
        surface_mat (list) : surfaces and type of modified parts of model
    """
    logger.debug("modifying model %s with ind %s" % (model.idfname, ind))
    surface_mat = []

    surface_mat.append(modify_walls(ind[0], model))
    surface_mat.append(modify_ceiling(ind[1], model))
    surface_mat.append(modify_floor(ind[2], model))
    surface_mat.append(modify_window(ind[3], model))

    return model, surface_mat


def duplicates(model, material):
    try:
        for mat in model.idfobjects["MATERIAL"]:
            if mat.Name == material.Name:
                logger.debug("Duplicate material")
                return True
    except Exception as e:
        logger.exception(e)
        pass


def modify_floor(ind_floor, model):
    """
    Modification of any floor connected to the outside by checking boundary
    condition

    args:
        ind (int): floor solution from optimization

    returns:
        surface.area (str) : surface of modified constructions
        surface.COnstruction_Name (str) : Name of modified construction
    """
    logger.debug("modify floor")
    area = 0
    construction_Name = None

    if ind_floor == 0:
        return area, construction_Name
    else:
        ind_floor -= 1

    if not duplicates(model, config.IDF_WALLS.idfobjects["MATERIAL"][ind_floor]):
        model.idfobjects["MATERIAL"].append(
            config.IDF_WALLS.idfobjects["MATERIAL"][ind_floor])
        model.idfobjects["CONSTRUCTION"].append(
            config.IDF_WALLS.idfobjects["CONSTRUCTION"][ind_floor])

    construction_Name = config.IDF_WALLS.idfobjects["CONSTRUCTION"][ind_floor].Name

    for surface in model.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if (surface.Surface_Type == "Floor" and
                surface.Outside_Boundary_Condition == "Ground"):
            surface.Construction_Name = config.IDF_WALLS.idfobjects["CONSTRUCTION"][ind_floor].Name
            area += surface.area
    return area, construction_Name


def modify_ceiling(ind_ceiling, model):
    """
    Modification of any ceiling connected to the outside by checking boundary
    condition

    args:
        ind (int): ceiling solution from optimization

    returns:
        surface.area (str) : surface of modified constructions
        surface.COnstruction_Name (str) : Name of modified construction
    """
    logger.debug("modify ceiling")
    area = 0
    construction_Name = None

    if ind_ceiling == 0:
        return area, construction_Name
    else:
        ind_ceiling -= 1

    if not duplicates(model, config.IDF_WALLS.idfobjects["MATERIAL"][ind_ceiling]):
        model.idfobjects["MATERIAL"].append(
            config.IDF_WALLS.idfobjects["MATERIAL"][ind_ceiling])
        model.idfobjects["CONSTRUCTION"].append(
            config.IDF_WALLS.idfobjects["CONSTRUCTION"][ind_ceiling])

    construction_Name = config.IDF_WALLS.idfobjects["CONSTRUCTION"][ind_ceiling].Name

    for surface in model.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if (surface.Surface_Type == "Roof" and
                surface.Outside_Boundary_Condition == "Outdoors"):
            surface.Construction_Name = config.IDF_WALLS.idfobjects["CONSTRUCTION"][ind_ceiling].Name
            area += surface.area
    return area, construction_Name


def modify_walls(ind_wall, model):
    """
    Modification of any walls connected to the outside by checking boundary
    condition

    args:
        ind (int): walls solution from optimization

    returns:
        surface.area (str) : surface of modified constructions
        surface.Construction_Name (str) : Name of modified construction
    """
    logger.debug("modify walls")
    area = 0
    construction_Name = None

    if ind_wall == 0:
        return area, construction_Name
    else:
        ind_wall -= 1

    if not duplicates(model, config.IDF_WALLS.idfobjects["MATERIAL"][ind_wall]):
        model.idfobjects["MATERIAL"].append(
            config.IDF_WALLS.idfobjects["MATERIAL"][ind_wall])
        model.idfobjects["CONSTRUCTION"].append(
            config.IDF_WALLS.idfobjects["CONSTRUCTION"][ind_wall])

    construction_Name = config.IDF_WALLS.idfobjects["CONSTRUCTION"][ind_wall].Name

    for surface in model.idfobjects["BUILDINGSURFACE:DETAILED"]:
        if (surface.Surface_Type == "Wall" and
                surface.Outside_Boundary_Condition == "Outdoors"):
            surface.Construction_Name = config.IDF_WALLS.idfobjects["CONSTRUCTION"][ind_wall].Name
            area += surface.area
    return area, construction_Name


def modify_window(ind_window, model):
    """
    Modification of any floor connected to the outside by checking boundary
    condition

    args:
        ind (int): window solution from optimization

    returns:
        amount (int) : number of modified windows

    """
    logger.debug("modify windows")
    area = 0
    window_name = None

    if ind_window == 0:
        return area, window_name
    else:
        ind_window -= 1

    model.idfobjects["WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"].append(
        config.IDF_WINDOWS.idfobjects["WINDOWMATERIAL:SIMPLEGLAZINGSYSTEM"][ind_window])
    model.idfobjects["CONSTRUCTION"].append(
        config.IDF_WINDOWS.idfobjects["CONSTRUCTION"][ind_window])

    for window in model.idfobjects["FENESTRATIONSURFACE:DETAILED"]:
        window.Construction_Name = config.IDF_WINDOWS.idfobjects["CONSTRUCTION"][ind_window].Name
        area += window.area
        window_name = window.Construction_Name
    return area, window_name


def economy(surface_mat):
    """
    Compute the price of a given retrofit plan given by the construction content and
    the window performance

    args:
        surface_mat (list): surface and composition of each type of wall (ext, ceiling, floor)

    returns:
        price (float) : total price of the retrofit measure
    """
    material = {"Polystyrene": "polystyrene_price",
                "Rockwool": "rockwool_price",
                "Glasswool": "glasswool_price",
                "Polyurethane": "polystyrene_price",
                "Window": "window_price"
                }
    price_mat = []
    mo = 0

    for paroi in surface_mat:
        if paroi[0] == 0:
            price_mat.append(0)
            continue
        try:
            price_this_mat = 0
            paroi_cont = paroi[1].split("_")[1]
            e = ast.literal_eval("".join(x for x in paroi_cont if x.isdigit()))
            mat = "".join(x for x in paroi_cont if not x.isdigit())

            price_this_mat, mo_mat = globals()[material[mat]](e)
            price_mat.append(paroi[0] * (price_this_mat + 10))  # +10 for coating
            mo += mo_mat
        # except TypeError:
        #     logger.error("eco: No modification on this part of model")
        #     import pdb; pdb.set_trace()
        #     pass
        except AttributeError:
            logger.error("eco : No price for %s" % (mat))
            pass

    price_mo = mo * 35  # 35€/h main d'oeuvre

    return price_mat  #+ price_mo  # + price_window


def window_price(e):
    e = float(e) / 10
    prices = {0.8: 130, 1.0: 150, 1.2: 170, 1.4: 190, 2: 245}

    price = prices[e]

    price = price + 49  # 49€ is flat price for arranging walls for construction

    return price, 0


def rockwool_price(e):
    return 0.6 * e + 1, 0.34


def glasswool_price(e):
    return 0.39 * e + 0.17, 0.34


def polystyrene_price(e):
    return 1.25 * e + 1, 0.29


def polyurethane_price(e):
    return 2 * e, 0.29


def overheating(result):
    logger.debug("computing overheating")
    indoor = None
    out = None

    for data in result:
        try:
            if "eplus.csv" in data[0]:
                logger.debug("found eplus.csv")
                out = data[1].iloc[:,
                                ["Outdoor Air Drybulb Temperature" in col for col in data[1].columns]]
                indoor = data[1].iloc[:, [
                    "Mean Air Temperature" in col for col in data[1].columns]]

                oh = 0
                for index in indoor.columns:
                    for temp in indoor[index]:
                        if temp > 26:
                            oh += temp - 0.31 * out.iat[indoor[index].values.tolist().index(temp), 0] + 17.8
                           
        except IndexError:
            if "eplusout.csv" in data[0]:
                logger.debug("found eplusout.csv")
                out = data[1].iloc[:,
                                ["Outdoor Air Drybulb Temperature" in col for col in data[1].columns]]
                indoor = data[1].iloc[:, [
                    "Mean Air Temperature" in col for col in data[1].columns]]

                oh = 0
                for index in indoor.columns:
                    for temp in indoor[index]:
                        if temp > 26:
                            oh += temp - 0.31 * out.iat[indoor[index].values.tolist().index(temp), 0] + 17.8

    logger.debug("overheating = %s °C/h" % (oh))
    return oh / 2 # /2 car demi heure sur l'échantillonage


def heating_needs(result):
    logger.debug("computing heating needs")
    for df in result:
        if "table" in df[0]:
            if df[1] is not None:
                try:
                    return ast.literal_eval(df[1].iat[1, 0])

                except Exception:
                    pass


def parse_csv(lines):
    for row in list(lines):
        for column in row:
            if "Total Site Energy" in column:
                i = row.index(column) + 1
                meter = row[i]
                logger.debug("In eplus-table.csv, %s kWh" % (meter))
                return pd.DataFrame([column, meter])


def process_table(filename, working_dir, simulname):
    import csv
    with open(filename, "rt") as f:
        file = csv.reader(f, delimiter=",")
        return parse_csv(file)


def evaluate_model(model, indb, surfacemat):
    """
    Simulation of a building model and post processing results to return
    comfort and heating demand

    args:
        model (IDF): model to simulation

    returns:
        results (tuple): heating demand and comfort

    ToDo:
        Windows
        overheating
    """
    custom_processes = {"*table.csv": process_table}

    logger.debug("computing price")
    price = np.array(economy(surfacemat)).sum()

    logger.debug("Price %s , lauching EP" % (price))

    start_time = time.time()
    logger.debug("running energyplus")
    result = ep.run_from_eppy(model, EPWFILE, idd_file=IDDPATH,
                              eplus_path=EPLUSPATH, keep_data=False,
                              custom_processes=custom_processes)
    logger.debug("Evaluation of %s in %s s" %
                     (model.idfname, time.time() - start_time))

    logger.debug("Computing objectives from result dataframes")
    heating = heating_needs(result)
    comfort = overheating(result)

    if "ClotFrancais" in model.idfname:
        logger.debug("Clot Francais found, adapting fitnesses")
        heating = heating * 10

    logger.debug("%s °C/h above 26°C" % (comfort))
    return heating, comfort, price


def evaluate(ind):
    """
    Evaluation function called by optimization. Deals with all the building
    of the building stock.

    args:
        ind (list): individual from genetic algorithm optimization

    returns:
        results (tuple): objective function

    ToDo
        put result in tuple
    """
#    ind = unconstrain(ind)
    indb = [ind[i:i + 4] for i in range(0, len(ind), 4)]
    surfacemat = []

    tot_area = sum(config.area.values())

    fitnesses = np.zeros(3)

    for building in config.buildings:
        epmodel = initialize(building)
        logger.info(building)
        build_library(epmodel, LIBFILE, LIBWINDOW, EPWFILE)
        logger.debug("modifying model %s" % (epmodel.idfname))
        epmodel, surfacemat = modify(
            indb[config.buildings.index(building)], epmodel)
        logger.debug("launching evaluation function")
        fitness = np.array(evaluate_model(epmodel, indb, surfacemat))
        logger.info("fitness for %s : %s" % (epmodel.idfname, fitness))
        fitnesses += fitness
        monitbuilding.info((ind, epmodel.idfname, fitness))
        
    logger.debug("dividing fitnesses by area")    
    fitnesses = fitnesses / tot_area
    logger.debug("returning fitnesses")

    return fitnesses


def price_per_phase(indb):
    price_phasing = []
    
    for building in config.buildings:
            epmodel = initialize(building)
            logger.debug("checking price for %s" % (building))
            build_library(epmodel, LIBFILE, LIBWINDOW, EPWFILE)
            logger.debug("modifying model %s" % (epmodel.idfname))
            epmodel, surfacemat = modify(
                indb[config.buildings.index(building)], epmodel)
            price = economy(surfacemat)
            price_phasing.append(price)
        
    price_phasing = [nitem for item in price_phasing for nitem in item]
    
    return price_phasing

def unconstrain(ind):
    """
    Constraints study by decision space limitation
    """
    new_ind = []
    logger.debug("unconstraining")
    for idx, item in enumerate(ind):
        if idx % 3 == 0:
            new_wall, new_window = change_bit(item)
            new_ind.append(new_wall)
            new_ind.append(ind[idx +1])
            new_ind.append(ind[idx +2])
            new_ind.append(new_window)
    logger.debug("unconstrained ind %s" % (new_ind))
    return new_ind

def change_bit(comb_bit):
    """
    From on gene for ext walls AND windows to 2 bits: one for walls one for windows
    """
    logger.debug("changing bit %s" % (comb_bit))
    if comb_bit % 43 == 0:
        inter = comb_bit + 6
        window = inter % 5
        wall = inter // 5 + 10 * (comb_bit // 43)

    elif comb_bit % 43 <= 2:
        window = comb_bit % 43
        wall = comb_bit // 43 * 10

    elif comb_bit % 43 <= 6:
        inter = comb_bit % 43 + 2
        window = inter - 5
        wall = comb_bit // 43 * 10 + 1

    elif comb_bit % 43 <= 36:
        inter = comb_bit % 43 + 3
        window = inter % 5
        wall = inter // 5 + 10 * (comb_bit // 43)
    
    elif comb_bit % 43 <= 40:
        inter = comb_bit % 43 + 4
        window = inter % 5
        wall = inter // 5 + 10 * (comb_bit // 43)

    elif comb_bit % 43 <= 43:
        inter = comb_bit % 43 + 6
        window = inter % 5
        wall = inter // 5 + 10 * (comb_bit // 43)

    logger.debug("returning new bits %s and %s" % (wall, window))
    return wall, window
