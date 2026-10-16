#include "lab2_methods.hpp"

namespace
{
    using Available = std::array<bool, PROBLEMSIZE>;

    const Node& findBestRegretNode(const Nodes& nodesArr, const Solution& solution, const Available& available)
    {
        return nodesArr[0];
    }
}

int greedyCycle2RegretHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution)
{
    return assessSolution(nodesArr, solution);
}

int greedyCycleWeightedSumHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution)
{
    return assessSolution(nodesArr, solution);
}

int nearestNeighbour2RegretHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution)
{
    return assessSolution(nodesArr, solution);
}

int nearestNeighbourWeightedSumHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution)
{
    return assessSolution(nodesArr, solution);
}