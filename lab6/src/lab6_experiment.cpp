#include "lab6_experiment.hpp"

#include "data_reader.hpp"
#include "metaheuristics.hpp"

#include <filesystem>
#include <iomanip>

namespace lab6
{
    namespace
    {
        void exportResult(const std::string &instance, const std::string &method, int run,
                          unsigned seed, double budgetMs, const SearchResult &result,
                          std::ostream &stream)
        {
            stream << std::setprecision(15) << instance << ',' << method << ',' << run << ",-1,"
                   << result.objective << ",\"";
            for (std::size_t i = 0; i < result.solution.size(); ++i)
                stream << (i == 0 ? "" : " ") << result.solution[i];
            stream << "\"," << result.elapsedMs << ',' << result.localSearchRuns << ','
                   << result.acceptedImprovements << ',' << result.initialObjective << ','
                   << seed << ',' << budgetMs << '\n';
            stream.flush();
        }

        double exportSummary(const std::string &instance, const std::string &method,
                             const std::vector<SearchResult> &runs, std::ostream &stream)
        {
            int minimum = runs.front().objective;
            int maximum = minimum;
            double total = 0, totalTime = 0, totalLS = 0;
            int minLS = runs.front().localSearchRuns, maxLS = minLS;
            for (const auto &run : runs)
            {
                minimum = std::min(minimum, run.objective);
                maximum = std::max(maximum, run.objective);
                total += run.objective;
                totalTime += run.elapsedMs;
                totalLS += run.localSearchRuns;
                minLS = std::min(minLS, run.localSearchRuns);
                maxLS = std::max(maxLS, run.localSearchRuns);
            }
            const double averageTime = totalTime / runs.size();
            stream << std::setprecision(15) << instance << ',' << method << ',' << minimum << ','
                   << maximum << ',' << total / runs.size() << ',' << averageTime << ','
                   << minLS << ',' << maxLS << ',' << totalLS / runs.size() << '\n';
            stream.flush();
            std::cout << method << ": min=" << minimum << ", max=" << maximum
                      << ", average=" << total / runs.size() << ", avg time=" << averageTime
                      << " ms, avg LS runs=" << totalLS / runs.size() << std::endl;
            return averageTime;
        }
    }

    void runExperimentForFile(const std::string &filename, int instanceIndex,
                              std::ostream &results, std::ostream &summary)
    {
        Nodes nodes{};
        readFile(filename.c_str(), nodes);
        calculateDistances(nodes);
        const auto instance = std::filesystem::path(filename).stem().string();
        std::cout << "Problem instance: " << instance << std::endl;
        std::vector<SearchResult> mslsRuns;
        for (int run = 0; run < EXPERIMENT_RUNS; ++run)
        {
            const unsigned seed = BASE_SEED + 1000 * instanceIndex + run;
            std::mt19937 generator(seed);
            auto result = multipleStartLocalSearch(nodes, generator);
            if (assessSolution(nodes, result.solution) != result.objective)
                throw std::runtime_error("MSLS objective/feasibility check failed");
            exportResult(instance, "MSLS", run, seed, 0.0, result, results);
            std::cout << "  MSLS " << run + 1 << '/' << EXPERIMENT_RUNS << ": "
                      << result.objective << ", " << result.elapsedMs << " ms" << std::endl;
            mslsRuns.push_back(std::move(result));
        }
        // Per-instance mean of ALL 20 complete MSLS runs, not of individual LS calls.
        const double budgetMs = exportSummary(instance, "MSLS", mslsRuns, summary);
        std::vector<SearchResult> ilsRuns;
        for (int run = 0; run < EXPERIMENT_RUNS; ++run)
        {
            // The first random start is shared with the corresponding MSLS run;
            // the two methods then use independent generator objects.
            const unsigned seed = BASE_SEED + 1000 * instanceIndex + run;
            std::mt19937 generator(seed);
            auto result = iteratedLocalSearch(nodes, generator,
                                             std::chrono::duration<double, std::milli>(budgetMs));
            if (assessSolution(nodes, result.solution) != result.objective)
                throw std::runtime_error("ILS objective/feasibility check failed");
            exportResult(instance, "ILS", run, seed, budgetMs, result, results);
            std::cout << "  ILS " << run + 1 << '/' << EXPERIMENT_RUNS << ": "
                      << result.objective << ", " << result.localSearchRuns << " LS calls" << std::endl;
            ilsRuns.push_back(std::move(result));
        }
        exportSummary(instance, "ILS", ilsRuns, summary);
    }
}
