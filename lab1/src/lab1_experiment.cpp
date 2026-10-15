#include "lab1_experiment.hpp"

#include "data_reader.hpp"
#include "experiment.hpp"
#include "greedy_methods.hpp"
#include "random_solution.hpp"

#include <iomanip>

void runExperimentForFile(const std::string &filename, std::ostream &results, std::ostream &summary)
{
    Nodes nodes{};
    readFile(filename.c_str(), nodes);
    calculateDistances(nodes);
    std::cout << "Problem instance: " << filename << '\n';

    const std::pair<std::string, Algorithm> methods[]{
        {"random", [](const Nodes &nodes, int, Solution &solution) {
             return randomSolution(nodes, solution);
         }},
        {"nearest_end", greedyNN1Solution},
        {"nearest_any", greedyNN2Solution},
        {"greedy_cycle", greedyCycleSolution}};

    for (const auto &[name, algorithm] : methods)
    {
        const auto stats = runExperiment(nodes, algorithm, filename, name, results, name != "random");
        summary << std::setprecision(12) << filename << ',' << name << ','
                << stats.minValue << ',' << stats.maxValue << ','
                << stats.average << ',' << stats.averageTimeMs << '\n';
        std::cout << name << ": min=" << stats.minValue << ", max=" << stats.maxValue
                  << ", average=" << stats.average
                  << ", avg time=" << stats.averageTimeMs << " ms/run\n";
    }
}
