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
    std::ofstream(resultsFilename) << "instance,method,run,start,objective,solution\n";
    for (const auto &filename : files)
        runExperimentForFile(filename, resultsFilename);

    return 0;
}