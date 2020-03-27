#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 13:51:11 2018

@author: yannis
"""
import random

def evaluate(ind):
    """
    Returns random values to the optimisation to speed up tests
    """
    conf = random.randint(10,1000)
    conso = random.randint(10,50)
    prix = random.randint(800,2000)
    
    return conf, conso, prix