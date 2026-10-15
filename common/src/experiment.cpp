#include "experiment.hpp"

#include <chrono>

ExperimentStats runExperiment(const Nodes &nodes, const Algorithm &algorithm,
                             const std::string &instance, const std::string &method,
                             std::ostream &results, bool usesStartNode)
{
    ExperimentStats stats;
    long long totalCost = 0;
    double totalTimeMs = 0.0;

    for (int run = 0; run < PROBLEMSIZE; ++run)
    {
        Solution solution{};
        const auto start = std::chrono::steady_clock::now();
        const int value = algorithm(nodes, run, solution);
        const auto end = std::chrono::steady_clock::now();

        stats.minValue = std::min(stats.minValue, value);
        stats.maxValue = std::max(stats.maxValue, value);
        totalCost += value;
        totalTimeMs += std::chrono::duration<double, std::milli>(end - start).count();

        results << instance << ',' << method << ',' << run << ','
                << (usesStartNode ? run : -1) << ',' << value << ",\"";
        for (std::size_t i = 0; i < solution.size(); ++i)
            results << (i == 0 ? "" : " ") << solution[i];
        results << "\"\n";
    }

    stats.average = static_cast<double>(totalCost) / PROBLEMSIZE;
    stats.averageTimeMs = totalTimeMs / PROBLEMSIZE;
    return stats;
}
