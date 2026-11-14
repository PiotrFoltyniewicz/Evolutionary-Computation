#include "lab6_experiment.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

int main(int argc, char *argv[])
{
    try
    {
        std::vector<std::string> files{"common/data/TSPA.csv", "common/data/TSPB.csv"};
        if (argc > 1)
            files.assign(argv + 1, argv + argc);
        // Reject malformed data before the fixed-size shared reader is called.
        for (const auto &filename : files)
        {
            std::ifstream input(filename);
            if (!input)
                throw std::runtime_error("Unable to open " + filename);
            int count = 0;
            std::string line;
            while (std::getline(input, line))
            {
                if (line.empty())
                    continue;
                std::istringstream row(line);
                int x, y, cost;
                char first, second;
                if (!(row >> x >> first >> y >> second >> cost) || first != ';' || second != ';')
                    throw std::runtime_error("Malformed row in " + filename);
                row >> std::ws;
                if (!row.eof())
                    throw std::runtime_error("Trailing data in " + filename);
                ++count;
            }
            if (count != 200)
                throw std::runtime_error(filename + " must contain exactly 200 nodes");
        }
        const std::filesystem::path outputDir{"lab6/out/generated"};
        std::filesystem::create_directories(outputDir);
        std::ofstream results(outputDir / "results.csv");
        std::ofstream summary(outputDir / "summary.csv");
        if (!results || !summary)
            throw std::runtime_error("Unable to open experiment outputs");
        results << "instance,method,run,start,objective,solution,time_ms,ls_runs,"
                   "accepted_improvements,initial_objective,seed,time_budget_ms\n";
        summary << "instance,method,min,max,average,average_time_ms,min_ls_runs,max_ls_runs,average_ls_runs\n";
        for (std::size_t i = 0; i < files.size(); ++i)
            lab6::runExperimentForFile(files[i], static_cast<int>(i), results, summary);
    }
    catch (const std::exception &error)
    {
        std::cerr << "lab6: " << error.what() << '\n';
        return 1;
    }
}
