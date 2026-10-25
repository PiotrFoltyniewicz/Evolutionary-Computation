#include "lab3_experiment.hpp"
#include "data_reader.hpp"
#include "experiment.hpp"
#include "lab2_methods.hpp"

#include <filesystem>
#include <iomanip>
#include <sstream>

int runLocalSearchVariant(const Nodes &nodes, int startNode, Solution &solution,
                          const LocalSearchVariant &variant,
                          const Algorithm &greedyConstructor)
{
    createStartingSolution(nodes, startNode, solution, variant.start,
                           greedyConstructor);
    return localSearch(nodes, solution, variant.search, variant.intraMove);
}

void runExperimentForFile(const std::string &filename, std::ostream &results, std::ostream &summary)
{
    Nodes nodes{};
    readFile(filename.c_str(), nodes);
    calculateDistances(nodes);
    const std::string instance = std::filesystem::path(filename).stem().string();
    std::cout << "Problem instance: " << instance << '\n';

    // Lowest mean objective in the previous labs; use weighted cycle for other instances.
    const Algorithm greedyConstructor = instance == "TSPB"
        ? nearestNeighbourWeightedSumHeuristics
        : greedyCycleWeightedSumHeuristics;

    for (const auto &variant : LOCAL_SEARCH_VARIANTS)
    {
        const Algorithm algorithm = [&](const Nodes &currentNodes, int startNode, Solution &solution) {
            return runLocalSearchVariant(currentNodes, startNode, solution, variant, greedyConstructor);
        };
        const bool usesStartNode = variant.start == StartingSolutionType::Greedy;
        const auto stats = runExperiment(nodes, algorithm, instance, variant.name, results, usesStartNode);

        summary << std::setprecision(12) << instance << ',' << variant.name << ','
                << stats.minValue << ',' << stats.maxValue << ','
                << stats.average << ',' << stats.averageTimeMs << '\n';
        std::cout << variant.name << ": min=" << stats.minValue << ", max=" << stats.maxValue
                  << ", average=" << stats.average
                  << ", avg time=" << stats.averageTimeMs << " ms/run\n";
    }

        
    std::ostringstream sink;  // wyniki nie są nikomu potrzebne, interesuje nas tylko czas
    const auto constructionStats = runExperiment(nodes, greedyConstructor, instance,
                                                "Construction", sink, true);
    const Algorithm randomStart = [](const Nodes &n, int s, Solution &sol) {
        return createStartingSolution(n, s, sol, StartingSolutionType::Random, {});
    };
    const auto randomStats = runExperiment(nodes, randomStart, instance,
                                        "RandomStart", sink, false);
    std::cout << instance << " construction avg ms: " << constructionStats.averageTimeMs
            << ", random start avg ms: " << randomStats.averageTimeMs << '\n';
}
