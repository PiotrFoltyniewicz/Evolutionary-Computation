#include "lab5_experiment.hpp"

#include "data_reader.hpp"
#include "experiment.hpp"
#include "local_search_methods.hpp"
#include "move_list_search.hpp"

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

    const std::pair<std::string, bool> methods[]{
        {"Steepest Edges Random", false},
        {"Move List Edges Random", true}
    };

    for (const auto &[name, useMoveList] : methods)
    {
        std::mt19937 generator(20261107); // Identical random starts for both methods.
        const Algorithm algorithm = [&](const Nodes &currentNodes, int, Solution &solution) {
            solution.resize(PROBLEMSIZE);
            std::iota(solution.begin(), solution.end(), 0);
            std::shuffle(solution.begin(), solution.end(), generator);
            solution.resize(SOLUTIONSIZE);
            return useMoveList
                ? moveListLocalSearch(currentNodes, solution)
                : steepestLocalSearch(currentNodes, solution, IntraRouteMove::EdgesExchange);
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
