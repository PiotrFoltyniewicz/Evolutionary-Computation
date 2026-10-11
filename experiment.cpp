#include "experiment.hpp"

#include <fstream>

ExperimentStats statsForValues(const std::vector<int> &values)
{
    ExperimentStats stats;
    long long sum = 0;

    for (int value : values)
    {
        stats.minValue = std::min(stats.minValue, value);
        stats.maxValue = std::max(stats.maxValue, value);
        sum += value;
    }

    if (!values.empty())
    {
        stats.average = static_cast<double>(sum) / static_cast<double>(values.size());
    }

    return stats;
}

ExperimentStats runGreedyExperiment(const Nodes &nodes, std::function<int(const Nodes &, int, Solution &)> algorithm)
{
    std::vector<int> values;
    values.reserve(PROBLEMSIZE);

    double totalTimeMs = 0.0;
    for (int startNode = 0; startNode < PROBLEMSIZE; ++startNode)
    {
        Solution solution{};
        const auto start = std::chrono::steady_clock::now();
        int value = algorithm(nodes, startNode, solution);
        const auto end = std::chrono::steady_clock::now();
        totalTimeMs += std::chrono::duration<double, std::milli>(end - start).count();
        values.push_back(value);
    }

    auto stats = statsForValues(values);
    stats.averageTimeMs = totalTimeMs / static_cast<double>(values.size());
    return stats;
}

ExperimentStats runRandomExperiment(const Nodes &nodes, int samples)
{
    std::vector<int> values;
    values.reserve(samples);

    double totalTimeMs = 0.0;
    for (int i = 0; i < samples; ++i)
    {
        Solution solution{};
        const auto start = std::chrono::steady_clock::now();
        int value = randomSolution(nodes, solution);
        const auto end = std::chrono::steady_clock::now();
        totalTimeMs += std::chrono::duration<double, std::milli>(end - start).count();
        values.push_back(value);
    }

    auto stats = statsForValues(values);
    stats.averageTimeMs = totalTimeMs / static_cast<double>(values.size());
    return stats;
}

void printExperimentSummary(const std::string &label, const ExperimentStats &stats)
{
    std::cout << label << ": min=" << stats.minValue
              << ", max=" << stats.maxValue
              << ", average=" << stats.average
              << ", avg time=" << stats.averageTimeMs << " ms/run\n";
}

void runExperimentForFile(const std::string &filename, const std::string &resultsFilename)
{
    Nodes nodes{};
    readFile(filename.c_str(), nodes);
    calculateDistances(nodes);

    std::cout << "Problem instance: " << filename << "\n";

    std::ofstream results(resultsFilename, std::ios::app);
    if (!results)
        throw std::runtime_error("Unable to open experiment results file");
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
    auto nn1Stats = runGreedyExperiment(nodes, greedyNN1Solution);
    auto nn2Stats = runGreedyExperiment(nodes, greedyNN2Solution);
    auto cycleStats = runGreedyExperiment(nodes, greedyCycleSolution);

    printExperimentSummary("Random (200 solutions)", randomStats);
    printExperimentSummary("Greedy NN1 (200 start nodes)", nn1Stats);
    printExperimentSummary("Greedy NN2 (200 start nodes)", nn2Stats);
    printExperimentSummary("Greedy Cycle (200 start nodes)", cycleStats);
    std::cout << "\n";
}
