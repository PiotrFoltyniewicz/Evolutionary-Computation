#pragma once

#include "types.hpp"

#include <chrono>
#include <random>

namespace lab6
{
    inline constexpr int EXPERIMENT_RUNS = 20;
    inline constexpr int MSLS_STARTS = 400;
    inline constexpr unsigned BASE_SEED = 20261114;

    struct SearchResult
    {
        Solution solution;
        int objective = 0;
        int initialObjective = 0; // First local optimum, before any perturbation/restart.
        int localSearchRuns = 0;
        int acceptedImprovements = 0;
        double elapsedMs = 0.0;
    };

    Solution randomStartingSolution(std::mt19937 &generator);
    int replacementCount(int consecutiveFailures);

    // Change both cycle topology and membership, preserving 100 distinct nodes.
    void perturb(Solution &solution, std::mt19937 &generator, int consecutiveFailures);

    SearchResult multipleStartLocalSearch(const Nodes &nodes, std::mt19937 &generator,
                                         int starts = MSLS_STARTS);
    // The initial LS is mandatory and included in both the timer and LS count.
    // An LS started before the deadline is completed, allowing one-call overrun.
    SearchResult iteratedLocalSearch(const Nodes &nodes, std::mt19937 &generator,
                                    std::chrono::duration<double, std::milli> budget);
}
