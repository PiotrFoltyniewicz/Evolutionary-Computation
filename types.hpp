#pragma once

#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
#include <list>
#include <numeric>
#include <stdexcept>
#include <string>
#include <vector>

constexpr int PROBLEMSIZE = 200;
constexpr int SOLUTIONSIZE = (PROBLEMSIZE - 1) / 2 + 1;

struct Node
{
    int x;
    int y;
    int cost;
    std::array<int, PROBLEMSIZE> distances{};
};

using Solution = std::array<int, SOLUTIONSIZE>;
using Nodes = std::array<Node, PROBLEMSIZE>;

inline int assessSolution(const Nodes &nodesArr, const Solution &solution)
{
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
