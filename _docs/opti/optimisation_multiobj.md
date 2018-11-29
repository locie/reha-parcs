---
title: "Formulation du problème"
category: "Optimisation Multiobjectif"
order: 1
---

Le problème d'optimisation multiobjectif doit être formulé avec notre problématique en intégrant les entrées, les paramètres et les sorties du problème

![Modèle de parc de bâtiment](../img/modele.png)

# Entrées du problème
## Modèle de parc de bâtiment

Au sein du projet, les entrées du problème sont le modèle de parc de bâtiment. Ce modèle décrit le parc de bâtiment et doit avoir un coût calculatoire assez faible pour être lancé une multitude de fois dans l'optimisation.

## Espace de décision de l'optimisation
L'algorithme d'optimisation explore des combinaison de l'espace de décision. Cet espace de décision est constitué de la description de toutes les mesures de rénovation pouvant être effectuées sur des parcs de bâtiments. Ces mesures peuvent être par exemple la modification de l'isolant d'un type de paroi, le changement de ventilation, ou encore la modification des émetteurs du système de chauffage.

# Paramètres du problème
Les paramètres correspondent aux grandeurs du modèles qui seront modifiés par les mesures de rénovation unitaires qui seront appliquées sur le modèle. Ici, les paramètres seront l'épaisseur d'isolation, le matériau d'isolation, la nature et la performance des menuiseries, la ventilation, ...

# Sorties du problèmes
Les sorties du problème sont les objectifs qui devront être maximisés ou minimisés par l'algorithme d'optimisation. Ces *fonctions objectif* seront:
* Les besoins énergétique du parc de bâtiment
* Un indicateur de surchauffe en °C.h
* Le coût total des travaux de la variante proposé (en €)
