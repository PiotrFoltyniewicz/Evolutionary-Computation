#include "lab7_experiment.hpp"
#include "lns.hpp"
#include "data_reader.hpp"

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>

namespace lab7
{
    namespace
    {
        double mslsBudget(const std::string &instance)
        {
            std::ifstream stream("lab6/out/generated/summary.csv");
            std::string line;
            std::getline(stream, line);
            while (std::getline(stream, line))
            {
                std::istringstream row(line);
                std::vector<std::string> fields;
                std::string field;
                while (std::getline(row, field, ','))
                    fields.push_back(field);
                if (fields.size() >= 6 && fields[0] == instance && fields[1] == "MSLS")
                {
                    const double budget = std::stod(fields[5]);
                    if (std::isfinite(budget) && budget > 0)
                        return budget;
                }
            }
            throw std::runtime_error("Missing valid lab6 MSLS budget for " + instance);
        }

        void exportResult(const std::string &instance, const std::string &method, int run,
                          unsigned seed, double budget, const SearchResult &result,
                          std::ostream &stream)
        {
            stream << std::setprecision(15) << instance << ',' << method << ',' << run << ",-1,"
                   << result.objective << ",\"";
            for (std::size_t i = 0; i < result.solution.size(); ++i)
                stream << (i == 0 ? "" : " ") << result.solution[i];
            stream << "\"," << result.elapsedMs << ',' << result.iterations << ','
                   << result.localSearchRuns << ',' << result.acceptedImprovements << ','
                   << result.initialObjective << ',' << seed << ',' << budget << '\n';
            stream.flush();
        }

        void exportSummary(const std::string &instance, const std::string &method,
                           const std::vector<SearchResult> &runs, std::ostream &stream)
        {
            int minimum = runs.front().objective, maximum = minimum;
            int minIterations = runs.front().iterations, maxIterations = minIterations;
            double total = 0, totalTime = 0, totalIterations = 0;
            for (const auto &run : runs)
            {
                minimum = std::min(minimum, run.objective);
                maximum = std::max(maximum, run.objective);
                minIterations = std::min(minIterations, run.iterations);
                maxIterations = std::max(maxIterations, run.iterations);
                total += run.objective;
                totalTime += run.elapsedMs;
                totalIterations += run.iterations;
            }
            stream << std::setprecision(15) << instance << ',' << method << ',' << minimum << ','
                   << maximum << ',' << total / runs.size() << ',' << totalTime / runs.size() << ','
                   << minIterations << ',' << maxIterations << ',' << totalIterations / runs.size() << '\n';
            stream.flush();
        }
    }

    void runExperimentForFile(const std::string &filename, int instanceIndex,
                              std::ostream &results, std::ostream &summary)
    {
        Nodes nodes{};
        readFile(filename.c_str(), nodes);
        calculateDistances(nodes);
        const auto instance = std::filesystem::path(filename).stem().string();
        const double budget = mslsBudget(instance);
        if (instance != "TSPA" && instance != "TSPB")
            throw std::invalid_argument("Repair selection requires TSPA or TSPB");
        const bool cycleRepair = instance == "TSPA";
        const std::array<std::string, 3> names{"Random Nodes", "Single Subpath", "Multiple Subpaths"};
        const std::array<Destroy, 3> operators{Destroy::RandomNodes, Destroy::SingleSubpath,
                                              Destroy::MultipleSubpaths};
        for (std::size_t i = 0; i < operators.size(); ++i)
            for (bool useLS : {false, true})
            {
                const std::string method = "LNS " + names[i] + (useLS ? " + LS" : "");
                std::vector<SearchResult> runs;
                for (int run = 0; run < RUNS; ++run)
                {
                    const unsigned seed = BASE_SEED + 1000 * instanceIndex + run;
                    std::mt19937 generator(seed);
                    auto result = largeNeighborhoodSearch(nodes, operators[i], useLS, cycleRepair,
                        generator, std::chrono::duration<double, std::milli>(budget));
                    if (assessSolution(nodes, result.solution) != result.objective)
                        throw std::runtime_error("LNS objective/feasibility check failed");
                    exportResult(instance, method, run, seed, budget, result, results);
                    std::cout << instance << ' ' << method << ' ' << run + 1 << '/' << RUNS
                              << ": " << result.objective << ", " << result.iterations
                              << " iterations" << std::endl;
                    runs.push_back(std::move(result));
                }
                exportSummary(instance, method, runs, summary);
            }
    }
}
