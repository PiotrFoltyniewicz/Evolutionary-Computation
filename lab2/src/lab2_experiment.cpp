#include "lab2_experiment.hpp"

#include "data_reader.hpp"
#include "experiment.hpp"
#include "lab2_methods.hpp"

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
        {"Greedy Cycle 2-regret heuristics", greedyCycle2RegretHeuristics},
        {"Greedy Cycle heuristics with a weighted sum criterion", greedyCycleWeightedSumHeuristics},
        {"NN heuristics 2-regret heuristics", nearestNeighbour2RegretHeuristics},
        {"NN heuristics with a weighted sum criterion", nearestNeighbourWeightedSumHeuristics}
    };

    for (const auto &[name, algorithm] : methods)
    {
        const auto stats = runExperiment(nodes, algorithm, instance, name, results, true);
        summary << std::setprecision(12) << instance << ',' << name << ','
                << stats.minValue << ',' << stats.maxValue << ','
                << stats.average << ',' << stats.averageTimeMs << '\n';
        std::cout << name << ": min=" << stats.minValue << ", max=" << stats.maxValue
                  << ", average=" << stats.average
                  << ", avg time=" << stats.averageTimeMs << " ms/run\n";
    }
}
