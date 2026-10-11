#include "experiment.hpp"

#include <fstream>
#include <filesystem>

int main(int argc, char *argv[])
{
    std::vector<std::string> files;

    if (argc > 1)
    {
        for (int i = 1; i < argc; ++i)
        {
            files.emplace_back(argv[i]);
        }
    }
    else
    {
        files = {"TSPA.csv", "TSPB.csv"};
    }

    const std::filesystem::path outputDir{"output"};
    std::filesystem::create_directories(outputDir);

    const std::string resultsFilename = (outputDir / "greedy_results.csv").string();
    const std::string summaryFilename = (outputDir / "greedy_summary.csv").string();
    std::ofstream(resultsFilename) << "instance,method,run,start,objective,solution\n";
    std::ofstream(summaryFilename) << "instance,method,min,max,average,average_time_ms\n";
    for (const auto &filename : files)
        runExperimentForFile(filename, resultsFilename, summaryFilename);

    return 0;
}