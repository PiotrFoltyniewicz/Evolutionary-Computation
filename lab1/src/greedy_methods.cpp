#include "greedy_methods.hpp"
#include "utils.hpp"

#include <limits>

int greedyNN1Solution(const Nodes &nodesArr, int startNodeIdx, Solution &solution)
{
    std::array<bool, PROBLEMSIZE> availableNodes;
    availableNodes.fill(true);
    availableNodes[startNodeIdx] = false;
    solution.clear();
    solution.reserve(SOLUTIONSIZE);
    solution.push_back(startNodeIdx);

    for (int position = 1; position < SOLUTIONSIZE; ++position)
    {
        const auto &current = nodesArr[solution[position - 1]];
        int bestCost = std::numeric_limits<int>::max();
        int bestNode = -1;
        for (int node = 0; node < PROBLEMSIZE; ++node)
        {
            if (!availableNodes[node])
                continue;
            const int cost = current.distances[node] + nodesArr[node].cost;
            if (cost < bestCost)
            {
                bestCost = cost;
                bestNode = node;
            }
        }
        solution.push_back(bestNode);
        availableNodes[bestNode] = false;
    }
    return assessSolution(nodesArr, solution);
}

int greedyNN2Solution(const Nodes &nodesArr, int startNodeIdx, Solution &solution)
{
    std::array<bool, PROBLEMSIZE> used{};
    solution.clear();
    solution.reserve(SOLUTIONSIZE);
    solution.push_back(startNodeIdx);
    used[startNodeIdx] = true;

    while (solution.size() < SOLUTIONSIZE)
    {
        const int size = static_cast<int>(solution.size());
        int bestCost = std::numeric_limits<int>::max();
        int bestNode = -1;
        int bestPosition = -1;

        for (int position = 0; position <= size; ++position)
        {
            for (int node = 0; node < PROBLEMSIZE; ++node)
            {
                if (used[node])
                    continue;
                const int cost = calculateInsertionCost(nodesArr, solution, node, position);

                if (cost < bestCost)
                {
                    bestCost = cost;
                    bestNode = node;
                    bestPosition = position;
                }
            }
        }
        solution.insert(solution.begin() + bestPosition, bestNode);
        used[bestNode] = true;
    }
    return assessSolution(nodesArr, solution);
}

int greedyCycleSolution(const Nodes &nodesArr, int startNodeIdx, Solution &solution)
{
    std::array<bool, PROBLEMSIZE> used{};
    solution.clear();
    solution.reserve(SOLUTIONSIZE);
    solution.push_back(startNodeIdx);
    used[startNodeIdx] = true;

    while (solution.size() < SOLUTIONSIZE)
    {
        const int size = static_cast<int>(solution.size());
        int bestCost = std::numeric_limits<int>::max();
        int bestNode = -1;
        int bestPosition = -1;

        for (int position = 1; position <= size; ++position)
        {
            for (int node = 0; node < PROBLEMSIZE; ++node)
            {
                if (used[node])
                    continue;
                const int cost = calculateInsertionCost(nodesArr, solution, node, position, true);

                if (cost < bestCost)
                {
                    bestCost = cost;
                    bestNode = node;
                    bestPosition = position;
                }
            }
        }
        solution.insert(solution.begin() + bestPosition, bestNode);
        used[bestNode] = true;
    }
    return assessSolution(nodesArr, solution);
}
