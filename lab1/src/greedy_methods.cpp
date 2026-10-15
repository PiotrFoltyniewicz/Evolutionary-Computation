#include "greedy_methods.hpp"

#include <limits>

int greedyNN1Solution(const Nodes &nodesArr, int startNodeIdx, Solution &solution)
{
    std::array<bool, PROBLEMSIZE> availableNodes;
    availableNodes.fill(true);
    availableNodes[startNodeIdx] = false;
    solution[0] = startNodeIdx;

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
        solution[position] = bestNode;
        availableNodes[bestNode] = false;
    }
    return assessSolution(nodesArr, solution);
}

int greedyNN2Solution(const Nodes &nodesArr, int startNodeIdx, Solution &solution)
{
    std::array<bool, PROBLEMSIZE> used{};
    solution[0] = startNodeIdx;
    used[startNodeIdx] = true;

    for (int size = 1; size < SOLUTIONSIZE; ++size)
    {
        int bestCost = std::numeric_limits<int>::max();
        int bestNode = -1;
        int bestPosition = -1;

        for (int position = 0; position <= size; ++position)
        {
            for (int node = 0; node < PROBLEMSIZE; ++node)
            {
                if (used[node])
                    continue;
                int cost = nodesArr[node].cost;
                if (position > 0)
                    cost += nodesArr[solution[position - 1]].distances[node];
                if (position < size)
                    cost += nodesArr[node].distances[solution[position]];
                if (position > 0 && position < size)
                    cost -= nodesArr[solution[position - 1]].distances[solution[position]];

                if (cost < bestCost)
                {
                    bestCost = cost;
                    bestNode = node;
                    bestPosition = position;
                }
            }
        }
        std::move_backward(solution.begin() + bestPosition,
                           solution.begin() + size, solution.begin() + size + 1);
        solution[bestPosition] = bestNode;
        used[bestNode] = true;
    }
    return assessSolution(nodesArr, solution);
}

int greedyCycleSolution(const Nodes &nodesArr, int startNodeIdx, Solution &solution)
{
    std::array<bool, PROBLEMSIZE> used{};
    solution[0] = startNodeIdx;
    used[startNodeIdx] = true;

    for (int size = 1; size < SOLUTIONSIZE; ++size)
    {
        int bestCost = std::numeric_limits<int>::max();
        int bestNode = -1;
        int bestPosition = -1;

        for (int position = 1; position <= size; ++position)
        {
            for (int node = 0; node < PROBLEMSIZE; ++node)
            {
                if (used[node])
                    continue;
                const int left = solution[position - 1];
                const int right = solution[position % size];
                const int cost = nodesArr[left].distances[node] +
                                 nodesArr[node].distances[right] -
                                 nodesArr[left].distances[right] + nodesArr[node].cost;

                if (cost < bestCost)
                {
                    bestCost = cost;
                    bestNode = node;
                    bestPosition = position;
                }
            }
        }
        std::move_backward(solution.begin() + bestPosition,
                           solution.begin() + size, solution.begin() + size + 1);
        solution[bestPosition] = bestNode;
        used[bestNode] = true;
    }
    return assessSolution(nodesArr, solution);
}
