#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

constexpr int PROBLEMSIZE = 200;
constexpr int SOLUTIONSIZE = (PROBLEMSIZE - 1) / 2 + 1;

struct Node
{
    int index;
    int x;
    int y;
    int cost;
    std::array<int, PROBLEMSIZE> distances{};
};

using Solution = std::vector<int>;

using Nodes = std::array<Node, PROBLEMSIZE>;

template <typename NodeType>
inline int assessSolution(const std::array<NodeType, PROBLEMSIZE> &nodesArr, const Solution &solution)
{
    if (solution.size() != SOLUTIONSIZE)
        return -1;

    std::array<bool, PROBLEMSIZE> used;
    used.fill(false);

    for (const auto& nodeIdx : solution)
    {
        if (nodeIdx < 0 || nodeIdx >= PROBLEMSIZE || used[nodeIdx])
            return -1;
        used[nodeIdx] = true;
    }

    int cost = 0;

    for (auto it = solution.begin(); std::next(it) != solution.end(); ++it)
    {
        cost += nodesArr[*it].distances[*std::next(it)] + nodesArr[*std::next(it)].cost;
    }

    cost += nodesArr[solution.back()].distances[solution.front()] + nodesArr[solution.front()].cost;
    return cost;
}

template <std::size_t N>
inline std::ostream &operator<<(std::ostream &os, const std::array<int, N> &arr)
{
    os << "[";
    for (std::size_t i = 0; i < N; ++i)
    {
        os << arr[i];
        if (i < N - 1)
            os << "->";
    }
    os << "]";
    return os;
}

inline std::ostream &operator<<(std::ostream &os, const Solution &solution)
{
    os << "[";
    for (std::size_t i = 0; i < solution.size(); ++i)
    {
        if (i > 0)
            os << "->";
        os << solution[i];
    }
    return os << "]";
}
