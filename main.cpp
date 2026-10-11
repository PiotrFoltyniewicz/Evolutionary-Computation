#include "experiment.hpp"

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

    for (const auto &filename : files)
    {
        runExperimentForFile(filename);
    }

    return 0;
}