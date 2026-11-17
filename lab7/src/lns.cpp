#include "lns.hpp"

#include "lab2_methods.hpp"
#include "metaheuristics.hpp"
#include "move_list_search.hpp"

namespace lab7
{
    namespace
    {
        // Uniformly sample a positive composition by choosing distinct cut points.
        std::vector<int> partition(int total, int parts, std::mt19937 &generator)
        {
            std::vector<int> cuts(total - 1);
            std::iota(cuts.begin(), cuts.end(), 1);
            std::shuffle(cuts.begin(), cuts.end(), generator);
            cuts.resize(parts - 1);
            cuts.push_back(0);
            cuts.push_back(total);
            std::sort(cuts.begin(), cuts.end());
            std::vector<int> lengths;
            for (int i = 0; i < parts; ++i)
                lengths.push_back(cuts[i + 1] - cuts[i]);
            return lengths;
        }
    }

    Solution destroy(const Solution &solution, Destroy method, std::mt19937 &generator)
    {
        if (solution.size() != SOLUTIONSIZE)
            throw std::invalid_argument("Destroy requires a full 100-node cycle");
        std::array<bool, PROBLEMSIZE> selected{};
        for (int node : solution)
        {
            if (node < 0 || node >= PROBLEMSIZE || selected[node])
                throw std::invalid_argument("Invalid cycle passed to destroy");
            selected[node] = true;
        }
        std::array<bool, SOLUTIONSIZE> removed{};
        if (method == Destroy::RandomNodes)
        {
            std::array<int, SOLUTIONSIZE> positions;
            std::iota(positions.begin(), positions.end(), 0);
            std::shuffle(positions.begin(), positions.end(), generator);
            for (int i = 0; i < REMOVED_NODES; ++i)
                removed[positions[i]] = true;
        }
        else
        {
            int parts = 1;
            if (method == Destroy::MultipleSubpaths)
                parts = std::uniform_int_distribution<int>(3, 5)(generator);
            else if (method != Destroy::SingleSubpath)
                throw std::invalid_argument("Unknown destroy operator");
            const auto lengths = partition(REMOVED_NODES, parts, generator);
            const auto gaps = partition(SOLUTIONSIZE - REMOVED_NODES, parts, generator);
            int position = std::uniform_int_distribution<int>(0, SOLUTIONSIZE - 1)(generator);
            // Positive survivor gaps keep the deleted subpaths disjoint on the cycle.
            for (int segment = 0; segment < parts; ++segment)
            {
                for (int i = 0; i < lengths[segment]; ++i)
                {
                    removed[position] = true;
                    position = (position + 1) % SOLUTIONSIZE;
                }
                position = (position + gaps[segment]) % SOLUTIONSIZE;
            }
        }
        Solution survivors;
        survivors.reserve(SOLUTIONSIZE);
        for (int i = 0; i < SOLUTIONSIZE; ++i)
            if (!removed[i])
                survivors.push_back(solution[i]);
        return survivors;
    }

    SearchResult largeNeighborhoodSearch(const Nodes &nodes, Destroy method,
                                        bool useLocalSearch, bool cycleRepair,
                                        std::mt19937 &generator,
                                        std::chrono::duration<double, std::milli> budget)
    {
        if (!std::isfinite(budget.count()) || budget.count() < 0)
            throw std::invalid_argument("LNS needs a finite nonnegative time budget");
        using Clock = std::chrono::steady_clock;
        const auto start = Clock::now();
        const auto deadline = start + budget;
        SearchResult best;
        best.solution = lab6::randomStartingSolution(generator);
        best.objective = moveListLocalSearch(nodes, best.solution);
        best.initialObjective = best.objective;
        best.localSearchRuns = 1;
        while (Clock::now() < deadline)
        {
            auto candidate = destroy(best.solution, method, generator);
            if (!cycleRepair)
            {
                const int origin = std::uniform_int_distribution<int>(0, candidate.size() - 1)(generator);
                std::rotate(candidate.begin(), candidate.begin() + origin, candidate.end());
            }
            int value = completeWeightedSumSolution(nodes, candidate, cycleRepair);
            if (useLocalSearch)
            {
                value = moveListLocalSearch(nodes, candidate);
                ++best.localSearchRuns;
            }
            ++best.iterations;
            if (value < best.objective)
            {
                best.objective = value;
                best.solution = std::move(candidate);
                ++best.acceptedImprovements;
            }
        }
        best.elapsedMs = std::chrono::duration<double, std::milli>(Clock::now() - start).count();
        return best;
    }
}
