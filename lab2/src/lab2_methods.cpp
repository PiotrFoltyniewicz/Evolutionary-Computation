#include "lab2_methods.hpp"

#include "utils.hpp"

#include <functional>
#include <limits>
#include <utility>

namespace
{
    using Available = std::array<bool, PROBLEMSIZE>;

    struct Regret
    {
        int value;
        int insertionCost;
        int position;
    };

    Regret calculateRegret(const Nodes& nodesArr, const Solution& solution, int nodeIdx, bool cycle)
    {
        int best = std::numeric_limits<int>::max();
        int secondBest = best;
        int insertionPosition = -1;
        for (int position = cycle; position <= static_cast<int>(solution.size()); ++position)
        {
            const int cost = calculateInsertionCost(nodesArr, solution, nodeIdx, position, cycle);
            if (cost < best)
            {
                secondBest = best;
                best = cost;
                insertionPosition = position;
            }
            else if (cost < secondBest)
            {
                secondBest = cost;
            }
        }

        int value;
        if (secondBest == std::numeric_limits<int>::max())
            value = 0;
        else
            value = secondBest - best;

        return {value, best, insertionPosition};
    }

    std::pair<int, int> findBestRegretNode(const Nodes& nodesArr, const Solution& solution,
                                         const Available& available, bool cycle)
    {
        int bestNode = -1;
        int bestPosition = -1;
        int bestRegret = -1;
        int lowestCost = std::numeric_limits<int>::max();

        for (int nodeIdx = 0; nodeIdx < PROBLEMSIZE; ++nodeIdx)
        {
            if (!available[nodeIdx])
                continue;

            const auto regret = calculateRegret(nodesArr, solution, nodeIdx, cycle);
            if (regret.value > bestRegret || (regret.value == bestRegret && regret.insertionCost < lowestCost))
            {
                bestRegret = regret.value;
                lowestCost = regret.insertionCost;
                bestNode = nodeIdx;
                bestPosition = regret.position;
            }
        }
        return {bestNode, bestPosition};
    }

    std::pair<int, int> findBestWeightedSumNode(const Nodes& nodesArr, const Solution& solution,
                                                const Available& available, bool cycle, double regretWeight)
    {
        int bestNode = -1;
        int bestPosition = -1;
        double lowestCost = std::numeric_limits<double>::infinity();

        for (int nodeIdx = 0; nodeIdx < PROBLEMSIZE; ++nodeIdx)
        {
            if (!available[nodeIdx])
                continue;

            const auto regret = calculateRegret(nodesArr, solution, nodeIdx, cycle);
            const double cost = (1.0 - regretWeight) * regret.insertionCost - regretWeight * regret.value;
        
            if (cost < lowestCost)
            {
                lowestCost = cost;
                bestNode = nodeIdx;
                bestPosition = regret.position;
            }
        }
        return {bestNode, bestPosition};
    }

    std::pair<int, int> findBestWeightedSumNode(const Nodes& nodesArr, const Solution& solution,
                                               const Available& available, bool cycle)
    {
        return findBestWeightedSumNode(nodesArr, solution, available, cycle, 0.5);
    }

    using NodeSelector = std::function<std::pair<int, int>(const Nodes&, const Solution&, const Available&, bool)>;

    int makeSolution(const Nodes& nodesArr, int startIdx, Solution& solution,
                      bool cycle, const NodeSelector& selectNode)
    {
        Available available;
        available.fill(true);
        available[startIdx] = false;
        solution.clear();
        solution.reserve(SOLUTIONSIZE);
        solution.push_back(startIdx);

        while (solution.size() < SOLUTIONSIZE)
        {
            const auto [nodeIdx, position] = selectNode(nodesArr, solution, available, cycle);
            solution.insert(solution.begin() + position, nodeIdx);
            available[nodeIdx] = false;
        }
        return assessSolution(nodesArr, solution);
    }
}

int greedyCycle2RegretHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution)
{
    return makeSolution(nodesArr, startIdx, solution, true, findBestRegretNode);
}

int greedyCycleWeightedSumHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution)
{
    return makeSolution(nodesArr, startIdx, solution, true, [](const Nodes& nodes, const Solution& current, const Available& available, bool cycle) {
        return findBestWeightedSumNode(nodes, current, available, cycle);
    });
}

int nearestNeighbour2RegretHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution)
{
    return makeSolution(nodesArr, startIdx, solution, false, findBestRegretNode);
}

int nearestNeighbourWeightedSumHeuristics(const Nodes& nodesArr, int startIdx, Solution& solution)
{
    return makeSolution(nodesArr, startIdx, solution, false, [](const Nodes& nodes, const Solution& current, const Available& available, bool cycle) {
        return findBestWeightedSumNode(nodes, current, available, cycle);
    });
}
