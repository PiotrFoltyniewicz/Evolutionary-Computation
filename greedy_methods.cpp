#include "greedy_methods.hpp"

#include <limits>

namespace
{
struct CyclePositionCache
{
    int leftNode = -1;
    int rightNode = -1;
    int bestNode = -1;
    int bestCost = std::numeric_limits<int>::max();
};

CyclePositionCache makeInvalidCyclePositionCache()
{
    return {};
}

CyclePositionCache buildCyclePositionCache(const Nodes &nodesArr,
                                          const std::array<bool, PROBLEMSIZE> &availableNodes,
                                          const Solution &solution,
                                          int position,
                                          int size)
{
    CyclePositionCache cache;
    cache.leftNode = solution[position];
    cache.rightNode = solution[(position + 1) % size];

    for (int candidate = 0; candidate < PROBLEMSIZE; ++candidate)
    {
        if (!availableNodes[candidate])
            continue;

        const int insertionCost = nodesArr[cache.leftNode].distances[candidate] +
                                  nodesArr[candidate].distances[cache.rightNode] -
                                  nodesArr[cache.leftNode].distances[cache.rightNode] +
                                  nodesArr[candidate].cost;

        if (insertionCost < cache.bestCost)
        {
            cache.bestCost = insertionCost;
            cache.bestNode = candidate;
        }
    }

    return cache;
}

bool isCyclePositionCacheValid(const CyclePositionCache &cache,
                               const Solution &solution,
                               int position,
                               int size,
                               const std::array<bool, PROBLEMSIZE> &availableNodes)
{
    return cache.leftNode == solution[position] &&
           cache.rightNode == solution[(position + 1) % size] &&
           cache.bestNode != -1 &&
           availableNodes[cache.bestNode];
}

std::vector<CyclePositionCache> shiftCyclePositionCache(const std::vector<CyclePositionCache> &cache, int insertPos)
{
    const int oldSize = static_cast<int>(cache.size());
    std::vector<CyclePositionCache> nextCache(oldSize + 1, makeInvalidCyclePositionCache());

    if (insertPos == 0)
    {
        for (int position = 0; position < oldSize - 1; ++position)
            nextCache[position + 1] = cache[position];
    }
    else if (insertPos == oldSize)
    {
        for (int position = 0; position < oldSize - 1; ++position)
            nextCache[position] = cache[position];
    }
    else
    {
        for (int position = 0; position < insertPos - 1; ++position)
            nextCache[position] = cache[position];

        for (int position = insertPos; position < oldSize; ++position)
            nextCache[position + 1] = cache[position];
    }

    return nextCache;
}
} // namespace

std::list<int>::const_iterator getNearsetNode(const std::list<int> &l, const Nodes &nodesArr, const Node &currNode)
{
    return std::min_element(
        l.begin(),
        l.end(),
        [&](int a, int b)
        {
            auto &nodeA = nodesArr[a];
            auto &nodeB = nodesArr[b];
            return (currNode.distances[a] + nodeA.cost) < (currNode.distances[b] + nodeB.cost);
        });
}

int greedyNN1Solution(const Nodes &nodesArr, int startNodeIdx, Solution &solution)
{
    std::list<int> possibleChoices(PROBLEMSIZE);
    std::iota(possibleChoices.begin(), possibleChoices.end(), 0);

    possibleChoices.remove(startNodeIdx);

    solution[0] = startNodeIdx;
    for (int i = 1; i < SOLUTIONSIZE; ++i)
    {
        const auto &currNode = nodesArr[solution[i - 1]];
        auto minIt = getNearsetNode(possibleChoices, nodesArr, currNode);

        solution[i] = *minIt;
        possibleChoices.erase(minIt);
    }

    return assessSolution(nodesArr, solution);
}

int greedyNN2Solution(const Nodes &nodesArr, int startNodeIdx, Solution &solution)
{
    using cost = int;
    using nodeIdx = int;

    std::array<bool, PROBLEMSIZE> availableNodes;
    availableNodes.fill(true);

    std::array<std::pair<cost, nodeIdx>, PROBLEMSIZE> cache;
    cache.fill({std::numeric_limits<cost>::max(), -1});

    solution[0] = startNodeIdx;
    availableNodes[startNodeIdx] = false;

    auto updateCache = [&](nodeIdx addedNode)
    {
        for (int j = 0; j < PROBLEMSIZE; ++j)
        {
            if (!availableNodes[j])
                continue;

            cost newCost = nodesArr[addedNode].distances[j] + nodesArr[j].cost;

            if (newCost < cache[j].first)
                cache[j] = {newCost, addedNode};
        }
    };

    updateCache(startNodeIdx);

    for (int i = 0; i < SOLUTIONSIZE - 1; ++i)
    {
        cost minCost = std::numeric_limits<cost>::max();
        nodeIdx newNode = -1;

        for (int j = 0; j < PROBLEMSIZE; ++j)
        {
            if (availableNodes[j] && cache[j].first < minCost)
            {
                minCost = cache[j].first;
                newNode = j;
            }
        }

        nodeIdx minNode = cache[newNode].second;

        auto minIt = std::find(
            solution.begin(),
            solution.begin() + i + 1,
            minNode);

        int minPos = std::distance(solution.begin(), minIt);

        cost beforeCost = nodesArr[minNode].distances[newNode];
        cost afterCost = beforeCost;

        if (minPos > 0)
        {
            beforeCost += nodesArr[solution[minPos - 1]].distances[newNode] - nodesArr[solution[minPos - 1]].distances[minNode];
        }

        if (minPos < i)
        {
            afterCost += nodesArr[solution[minPos + 1]].distances[newNode] - nodesArr[solution[minPos + 1]].distances[minNode];
        }

        int insertPos = minPos + (afterCost < beforeCost);

        std::move_backward(
            solution.begin() + insertPos,
            solution.begin() + i + 1,
            solution.begin() + i + 2);

        solution[insertPos] = newNode;

        availableNodes[newNode] = false;
        updateCache(newNode);
    }

    return assessSolution(nodesArr, solution);
}

int greedyCycleSolution(const Nodes &nodesArr, int startNodeIdx, Solution &solution)
{
    std::array<bool, PROBLEMSIZE> availableNodes;
    availableNodes.fill(true);

    std::vector<CyclePositionCache> positionCache;
    positionCache.reserve(SOLUTIONSIZE);

    solution[0] = startNodeIdx;
    availableNodes[startNodeIdx] = false;

    int nearestNode = -1;
    int minDistance = std::numeric_limits<int>::max();

    for (int j = 0; j < PROBLEMSIZE; ++j)
    {
        if (!availableNodes[j])
            continue;

        int distance = nodesArr[startNodeIdx].distances[j];

        if (distance < minDistance)
        {
            minDistance = distance;
            nearestNode = j;
        }
    }

    solution[1] = nearestNode;
    availableNodes[nearestNode] = false;

    positionCache.push_back(makeInvalidCyclePositionCache());
    positionCache.push_back(makeInvalidCyclePositionCache());

    for (int size = 2; size < SOLUTIONSIZE; ++size)
    {
        int bestNode = -1;
        int bestInsertPos = -1;
        int bestCost = std::numeric_limits<int>::max();

        for (int position = 0; position < size; ++position)
        {
            auto &cacheEntry = positionCache[position];
            if (!isCyclePositionCacheValid(cacheEntry, solution, position, size, availableNodes))
                cacheEntry = buildCyclePositionCache(nodesArr, availableNodes, solution, position, size);

            if (cacheEntry.bestCost < bestCost)
            {
                bestCost = cacheEntry.bestCost;
                bestNode = cacheEntry.bestNode;
                bestInsertPos = position + 1;
            }
        }

        std::move_backward(
            solution.begin() + bestInsertPos,
            solution.begin() + size,
            solution.begin() + size + 1);

        solution[bestInsertPos] = bestNode;
        availableNodes[bestNode] = false;

        positionCache = shiftCyclePositionCache(positionCache, bestInsertPos);
    }

    return assessSolution(nodesArr, solution);
}
