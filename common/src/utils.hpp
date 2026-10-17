#pragma once

#include "types.hpp"

#include <cassert>

inline int calculateInsertionCost(const Nodes &nodesArr, const Solution &solution,
                                  int nodeIdx, int position, bool closedCycle = false)
{
    assert(!solution.empty());
    assert(position >= 0 && position <= static_cast<int>(solution.size()));
    assert(nodeIdx >= 0 && nodeIdx < PROBLEMSIZE);

    int left = -1;
    int right = -1;

    if (position > 0)
        left = solution[position - 1];
    else if (closedCycle)
        left = solution.back();

    if (position < static_cast<int>(solution.size()))
        right = solution[position];
    else if (closedCycle)
        right = solution[0];

    const Node& node = nodesArr[nodeIdx];
    int cost = node.cost;
    if (left != -1)
        cost += nodesArr[left].distances[node.index];
    if (right != -1)
        cost += nodesArr[node.index].distances[right];
    if (left != -1 && right != -1)
        cost -= nodesArr[left].distances[right];
    return cost;
}
