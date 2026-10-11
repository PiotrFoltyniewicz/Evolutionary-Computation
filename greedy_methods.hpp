#pragma once

#include "types.hpp"

std::list<int>::const_iterator getNearsetNode(const std::list<int> &l, const Nodes &nodesArr, const Node &currNode);
int greedyNN1Solution(const Nodes &nodesArr, int startNodeIdx, Solution &solution);
int greedyNN2Solution(const Nodes &nodesArr, int startNodeIdx, Solution &solution);
int greedyCycleSolution(const Nodes &nodesArr, int startNodeIdx, Solution &solution);
