#include "metaheuristics.hpp"

#include "move_list_search.hpp"

#include <limits>

namespace lab6
{
    namespace
    {
        using Clock = std::chrono::steady_clock;

        double elapsedMs(Clock::time_point start)
        {
            return std::chrono::duration<double, std::milli>(Clock::now() - start).count();
        }
    }

    Solution randomStartingSolution(std::mt19937 &generator)
    {
        Solution solution(PROBLEMSIZE);
        std::iota(solution.begin(), solution.end(), 0);
        std::shuffle(solution.begin(), solution.end(), generator);
        solution.resize(SOLUTIONSIZE);
        return solution;
    }

    int replacementCount(int consecutiveFailures)
    {
        if (consecutiveFailures < 0)
            throw std::invalid_argument("Negative failure count");
        return 2 + 2 * std::min(consecutiveFailures / 50, 3);
    }

    void perturb(Solution &solution, std::mt19937 &generator, int consecutiveFailures)
    {
        if (solution.size() != SOLUTIONSIZE)
            throw std::invalid_argument("Perturbation requires a 100-node cycle");
        std::array<bool, PROBLEMSIZE> selected{};
        for (const int node : solution)
        {
            if (node < 0 || node >= PROBLEMSIZE || selected[node])
                throw std::invalid_argument("Invalid perturbation input");
            selected[node] = true;
        }
        const int replacements = replacementCount(consecutiveFailures);
        std::vector<int> outside;
        for (int node = 0; node < PROBLEMSIZE; ++node)
            if (!selected[node])
                outside.push_back(node);
        std::array<int, SOLUTIONSIZE> positions;
        std::iota(positions.begin(), positions.end(), 0);
        std::shuffle(positions.begin(), positions.end(), generator);
        std::shuffle(outside.begin(), outside.end(), generator);
        for (int i = 0; i < replacements; ++i)
            solution[positions[i]] = outside[i];

        // A uniformly chosen origin makes the closing edge eligible for a cut.
        std::uniform_int_distribution<int> origin(0, SOLUTIONSIZE - 1);
        std::rotate(solution.begin(), solution.begin() + origin(generator), solution.end());
        // Uniformly sample 3 internal boundaries, rejecting segments shorter
        // than 2. Together with the origin these define 4 nonadjacent cuts.
        std::array<int, SOLUTIONSIZE - 1> boundaries;
        std::iota(boundaries.begin(), boundaries.end(), 1);
        std::array<int, 3> cuts;
        do
        {
            std::shuffle(boundaries.begin(), boundaries.end(), generator);
            std::copy_n(boundaries.begin(), 3, cuts.begin());
            std::sort(cuts.begin(), cuts.end());
        } while (cuts[0] < 2 || cuts[1] - cuts[0] < 2 ||
                 cuts[2] - cuts[1] < 2 || SOLUTIONSIZE - cuts[2] < 2);

        // A|B|C|D -> A|D|C|B, without reversing segments (double bridge).
        Solution reordered;
        reordered.reserve(SOLUTIONSIZE);
        const auto append = [&](int begin, int end) {
            reordered.insert(reordered.end(), solution.begin() + begin, solution.begin() + end);
        };
        append(0, cuts[0]);
        append(cuts[2], SOLUTIONSIZE);
        append(cuts[1], cuts[2]);
        append(cuts[0], cuts[1]);
        solution = std::move(reordered);
    }

    SearchResult multipleStartLocalSearch(const Nodes &nodes, std::mt19937 &generator, int starts)
    {
        if (starts <= 0)
            throw std::invalid_argument("MSLS needs at least one local search");
        const auto start = Clock::now();
        SearchResult best;
        best.objective = std::numeric_limits<int>::max();
        for (int i = 0; i < starts; ++i)
        {
            auto candidate = randomStartingSolution(generator);
            const int value = moveListLocalSearch(nodes, candidate);
            ++best.localSearchRuns;
            if (i == 0)
                best.initialObjective = value;
            if (value < best.objective)
            {
                if (i > 0)
                    ++best.acceptedImprovements;
                best.objective = value;
                best.solution = std::move(candidate);
            }
        }
        best.elapsedMs = elapsedMs(start);
        return best;
    }

    SearchResult iteratedLocalSearch(const Nodes &nodes, std::mt19937 &generator,
                                    std::chrono::duration<double, std::milli> budget)
    {
        if (!std::isfinite(budget.count()) || budget.count() < 0)
            throw std::invalid_argument("ILS needs a finite nonnegative time budget");
        const auto start = Clock::now();
        const auto deadline = start + budget;
        SearchResult best;
        best.solution = randomStartingSolution(generator);
        best.objective = moveListLocalSearch(nodes, best.solution);
        best.initialObjective = best.objective;
        best.localSearchRuns = 1;
        int consecutiveFailures = 0;
        while (Clock::now() < deadline)
        {
            auto candidate = best.solution;
            perturb(candidate, generator, consecutiveFailures);
            // Do not launch a new LS if the perturbation used the remaining time.
            if (Clock::now() >= deadline)
                break;
            const int value = moveListLocalSearch(nodes, candidate);
            ++best.localSearchRuns;
            if (value < best.objective)
            {
                best.objective = value;
                best.solution = std::move(candidate);
                ++best.acceptedImprovements;
                consecutiveFailures = 0;
            }
            else
                ++consecutiveFailures;
        }
        best.elapsedMs = elapsedMs(start);
        return best;
    }
}
