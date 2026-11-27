#include "lab8_experiment.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

int main()
{
    try
    {
        const std::filesystem::path outputDir{"lab8/out/generated"};
        std::filesystem::create_directories(outputDir);
        std::ofstream results(outputDir / "results.csv");
        if (!results)
            throw std::runtime_error("Unable to open results.csv");

        results << "instance,method,run,start,objective,solution\n";
        for (const auto &filename : {"common/data/TSPA.csv", "common/data/TSPB.csv"})
            lab8::runExperimentForFile(filename, results);

        results.close();
        if (!results)
            throw std::runtime_error("Unable to write results.csv");
    }
    catch (const std::exception &error)
    {
        std::cerr << "lab8: " << error.what() << '\n';
        return 1;
    }
}
