#include "lab1_experiment.hpp"

#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <vector>

int main(int argc, char *argv[])
{
    std::vector<std::string> files{"common/data/TSPA.csv", "common/data/TSPB.csv"};
    if (argc > 1)
        files.assign(argv + 1, argv + argc);

    const std::filesystem::path outputDir{"lab1/out/generated"};
    std::filesystem::create_directories(outputDir);
    std::ofstream results(outputDir / "greedy_results.csv");
    std::ofstream summary(outputDir / "greedy_summary.csv");
    if (!results || !summary)
        throw std::runtime_error("Unable to open experiment output files");

    results << "instance,method,run,start,objective,solution\n";
    summary << "instance,method,min,max,average,average_time_ms\n";
    for (const auto &filename : files)
        runExperimentForFile(filename, results, summary);
}
