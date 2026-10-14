#include "lab1_experiment.hpp"

#include "data_reader.hpp"
#include "greedy_methods.hpp"
#include "random_solution.hpp"

#include <filesystem>
#include <fstream>

static void writeSummaryRow(std::ofstream &summary, const std::string &filename, const std::string &method, const ExperimentStats &stats)
{
    summary << filename << "," << method << "," << stats.minValue << "," << stats.maxValue << ","
            << stats.average << "," << stats.averageTimeMs << "\n";
}

void runExperimentForFile(const std::string &filename, const std::string &resultsFilename, const std::string &summaryFilename)
{
    Nodes nodes{};
    readFile(filename.c_str(), nodes);
    calculateDistances(nodes);

    std::cout << "Problem instance: " << filename << "\n";

    const std::filesystem::path resultsPath{resultsFilename};
    if (resultsPath.has_parent_path())
        std::filesystem::create_directories(resultsPath.parent_path());

    const std::filesystem::path summaryPath{summaryFilename};
    if (summaryPath.has_parent_path())
        std::filesystem::create_directories(summaryPath.parent_path());

    std::ofstream results(resultsFilename, std::ios::app);
    if (!results)
        throw std::runtime_error("Unable to open experiment results file");

    std::ofstream summary(summaryFilename, std::ios::app);
    if (!summary)
        throw std::runtime_error("Unable to open experiment summary file");

    auto writeResult = [&](const std::string &method, int run, int start, const Solution &solution, int value)
    {
        results << filename << "," << method << "," << run << "," << start << "," << value << ",\"";
        for (std::size_t i = 0; i < solution.size(); ++i)
            results << (i == 0 ? "" : " ") << solution[i];
        results << "\"\n";
    };

    for (int run = 0; run < 200; ++run)
    {
        Solution solution{};
        const int value = randomSolution(nodes, solution);
        writeResult("random", run, -1, solution, value);
    }
    const std::vector<std::pair<std::string, std::function<int(const Nodes &, int, Solution &)>>> algorithms{
        {"nearest_end", greedyNN1Solution},
        {"nearest_any", greedyNN2Solution},
        {"greedy_cycle", greedyCycleSolution}};
    for (const auto &[method, algorithm] : algorithms)
    {
        for (int start = 0; start < PROBLEMSIZE; ++start)
        {
            Solution solution{};
            writeResult(method, start, start, solution, algorithm(nodes, start, solution));
        }
    }

    auto randomStats = runRandomExperiment(nodes, 200);
    auto nn1Stats = runStartNodeExperiment(nodes, greedyNN1Solution);
    auto nn2Stats = runStartNodeExperiment(nodes, greedyNN2Solution);
    auto cycleStats = runStartNodeExperiment(nodes, greedyCycleSolution);

    writeSummaryRow(summary, filename, "random", randomStats);
    writeSummaryRow(summary, filename, "nearest_end", nn1Stats);
    writeSummaryRow(summary, filename, "nearest_any", nn2Stats);
    writeSummaryRow(summary, filename, "greedy_cycle", cycleStats);

    printExperimentSummary("Random (200 solutions)", randomStats);
    printExperimentSummary("Greedy NN1 (200 start nodes)", nn1Stats);
    printExperimentSummary("Greedy NN2 (200 start nodes)", nn2Stats);
    printExperimentSummary("Greedy Cycle (200 start nodes)", cycleStats);
    std::cout << "\n";
}
