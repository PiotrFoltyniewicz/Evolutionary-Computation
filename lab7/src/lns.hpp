#pragma once

#include "types.hpp"
#include <chrono>
#include <random>

namespace lab7
{
    inline constexpr int RUNS = 20;
    inline constexpr unsigned BASE_SEED = 20261117;
    inline constexpr int REMOVED_NODES = 30;
    enum class Destroy { RandomNodes, SingleSubpath, MultipleSubpaths };

    struct SearchResult
    {
        Solution solution;
        int objective = 0;
        int initialObjective = 0;
        int iterations = 0;
        int localSearchRuns = 0;
        int acceptedImprovements = 0;
        double elapsedMs = 0;
    };

    // Retains cyclic order and removes exactly 30 nodes from a valid full cycle.
    Solution destroy(const Solution &solution, Destroy method, std::mt19937 &generator);
    SearchResult largeNeighborhoodSearch(const Nodes &nodes, Destroy method,
                                        bool useLocalSearch, bool cycleRepair,
                                        std::mt19937 &generator,
                                        std::chrono::duration<double, std::milli> budget);
}
