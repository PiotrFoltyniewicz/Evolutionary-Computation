#include "experiment.hpp"

#include <fstream>

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

    const std::string resultsFilename = "Reports/experiment_results.csv";
    std::ofstream(resultsFilename) << "instance,method,run,start,objective,solution\n";
    for (const auto &filename : files)
        runExperimentForFile(filename, resultsFilename);

    return 0;
}