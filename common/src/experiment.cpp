#include "experiment.hpp"

#include "random_solution.hpp"

#include <chrono>

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

ExperimentStats runStartNodeExperiment(const Nodes &nodes, std::function<int(const Nodes &, int, Solution &)> algorithm)
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

