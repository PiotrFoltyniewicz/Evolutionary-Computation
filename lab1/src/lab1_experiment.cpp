#include "lab1_experiment.hpp"

#include "data_reader.hpp"
#include "experiment.hpp"
#include "greedy_methods.hpp"
#include "random_solution.hpp"

#include <filesystem>
#include <iomanip>

void runExperimentForFile(const std::string &filename, std::ostream &results, std::ostream &summary)
{
    Nodes nodes{};
    readFile(filename.c_str(), nodes);
    calculateDistances(nodes);
    const std::string instance = std::filesystem::path(filename).stem().string();
    std::cout << "Problem instance: " << instance << '\n';

    const std::pair<std::string, Algorithm> methods[]{
        {"Random", [](const Nodes &nodes, int, Solution &solution) {
             return randomSolution(nodes, solution);
         }},
        {"Nearest Node End", greedyNN1Solution},
        {"Nearest Node Any", greedyNN2Solution},
        {"Greedy Cycle", greedyCycleSolution}};

    for (const auto &[name, algorithm] : methods)
    {
        const auto stats = runExperiment(nodes, algorithm, instance, name, results, name != "Random");
        summary << std::setprecision(12) << instance << ',' << name << ','
                << stats.minValue << ',' << stats.maxValue << ','
                << stats.average << ',' << stats.averageTimeMs << '\n';
        std::cout << name << ": min=" << stats.minValue << ", max=" << stats.maxValue
                  << ", average=" << stats.average
                  << ", avg time=" << stats.averageTimeMs << " ms/run\n";
    }
}
