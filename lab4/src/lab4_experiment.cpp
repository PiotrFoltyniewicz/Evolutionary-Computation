#include "lab4_experiment.hpp"

#include "candidate_search.hpp"
#include "data_reader.hpp"
#include "experiment.hpp"
#include "local_search_methods.hpp"

#include <filesystem>
#include <iomanip>
#include <numeric>
#include <random>

void runExperimentForFile(const std::string &filename, std::ostream &results, std::ostream &summary)
{
    Nodes nodes{};
    readFile(filename.c_str(), nodes);
    calculateDistances(nodes);
    const std::string instance = std::filesystem::path(filename).stem().string();
    std::cout << "Problem instance: " << instance << '\n';

    const std::pair<std::string, int> methods[]{
        {"Steepest Edges Random", 0},
        {"Candidate Edges k5 Random", 5},
        {"Candidate Edges k10 Random", 10},
        {"Candidate Edges k20 Random", 20}
    };

    for (const auto &[name, k] : methods)
    {
        const auto candidates = k == 0 ? CandidateLists{} : buildCandidateLists(nodes, k);
        std::mt19937 generator(20261031); // The same sequence of starts for each method.
        const Algorithm algorithm = [&](const Nodes &currentNodes, int, Solution &solution) {
            solution.resize(PROBLEMSIZE);
            std::iota(solution.begin(), solution.end(), 0);
            std::shuffle(solution.begin(), solution.end(), generator);
            solution.resize(SOLUTIONSIZE);
            return k == 0
                ? steepestLocalSearch(currentNodes, solution, IntraRouteMove::EdgesExchange)
                : steepestLocalSearch(currentNodes, solution, candidates);
        };
        const auto stats = runExperiment(nodes, algorithm, instance, name, results, false);
        summary << std::setprecision(12) << instance << ',' << name << ','
                << stats.minValue << ',' << stats.maxValue << ','
                << stats.average << ',' << stats.averageTimeMs << '\n';
        std::cout << name << ": min=" << stats.minValue << ", max=" << stats.maxValue
                  << ", average=" << stats.average
                  << ", avg time=" << stats.averageTimeMs << " ms/run\n";
    }
}
