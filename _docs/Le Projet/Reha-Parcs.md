---
title: Description
category: "Le Projet"
order: 1
---
En construction.

Le but du projet est de créer un outil interactif d'aide à la décision pour la rénovation énérgétique des parcs de bâtiment. Il allie des méthodes numériques appliquées à l'échelle du parc de bâtiment.
Les parcs de bâtiment visés par le projet ont les caractéristiques suivantes:
* Les parcs sont gérés par la même entitée qui gère le budget et le déroulé global des travaux
* Les parcs de bâtiment n'ont pas forcément d'unicité de lieu
* Le nombre de bâtiments est classiquement compris entre 10 et 150 bâtiments

Le projet est constitué de 5 tâches:
![Description du projet Reha-Parcs](./images/project.png)

## Tâche 1:
La tâche 1 consiste à poser le problème d'optimisation multiobjectif: ses entrées, ses paramètres et ses sorties. Elle délimite aussi l'étendue de l'espace de décision correspondant aux travaux possibles sur le parc de bâtiment.
Cette tâche est réalisée par le CEA et ITF.

## Tâche 2:
Le parc de bâtiment peut être constitué de plusieurs centaines de bâtiments. Afin de pouvoir lancer une optimisation multiobjectif sur le parc entier, la tâche 2 s'insère afin de réduire le modèle de parc de bâtiments. Dans cette tâche, des méthodes de clustering sont développées afin de générer des archetypes de bâtiments cohérent avant mais aussi après rénovation.
La tâche 2 est réalisée par le CSTB

## Tâche 3:
Afin de sélectionner les mesures optimales pour la réhabilitation du parc de bâtiment, la tâche 3 utilise l'optimisation multiobjectifs dans le but d'obtenir les meilleures performances du parc de bâtiment du point de vue de la consommation énergétique, du coût économique et du confort des occupants.
Cette tâche est réalisée par le LOCIE

## Tâche 4:
La tâche 3 fournit à la tâche 4 une multitude de solutions Pareto-optimales. Cette dernière permet grâce à l'utilisation de méthode d'aide à la décision de manière interactive de sélectionner les quelques solutions les plus adaptées pour le décideur sur des critères objectifs et chiffrés mais aussi sur des critères subjectifs pouvant être politiques, sociaux, ou autres.
Cette tâche est réalisée par I2M

## Tâche 5:
Il s'agit de l'application des tâches précédentes à un cas d'étude. Pour Réha-Parcs, le cas d'étude sélectionné est un parc de 130 logement sociaux situés dans une commune limitrophe à Paris.
