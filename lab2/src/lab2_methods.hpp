#pragma once

#include "types.hpp"

int greedyCycle2RegretHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution);
int greedyCycleWeightedSumHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution);

int nearestNeighbour2RegretHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution);
int nearestNeighbourWeightedSumHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution);
// Complete an existing partial cycle/path with the same weighted-regret selector.
int completeWeightedSumSolution(const Nodes& nodesArr, Solution& solution, bool cycle);
