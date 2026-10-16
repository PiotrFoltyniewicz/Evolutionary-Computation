#pragma once

#include "types.hpp"

int greedyCycle2RegretHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution);
int greedyCycleWeightedSumHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution);

int nearestNeighbour2RegretHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution);
int nearestNeighbourWeightedSumHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution);