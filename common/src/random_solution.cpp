#include "random_solution.hpp"

#include <random>

int randomSolution(const Nodes &nodesArr, Solution &solution)
{
    std::random_device rd;
    std::mt19937 gen(rd());

    std::array<int, PROBLEMSIZE> indexes{};
    std::iota(indexes.begin(), indexes.end(), 0);

    std::shuffle(indexes.begin(), indexes.end(), gen);
    std::copy_n(indexes.begin(), solution.size(), solution.begin());

    return assessSolution(nodesArr, solution);
}
