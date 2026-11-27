#include "lab8_experiment.hpp"

#include "data_reader.hpp"
#include "local_search_methods.hpp"
#include "random_solution.hpp"

#include <filesystem>

namespace lab8
{
    void runExperimentForFile(const std::string &filename, std::ostream &results)
    {
        constexpr int runs = 1000;
        Nodes nodes{};
        readFile(filename.c_str(), nodes);
        calculateDistances(nodes);

        const auto instance = std::filesystem::path(filename).stem().string();
        for (int run = 0; run < runs; ++run)
        {
            Solution solution;
            randomSolution(nodes, solution);
            const int objective = greedyLocalSearch(nodes, solution, IntraRouteMove::EdgesExchange);
            if (objective != assessSolution(nodes, solution))
                throw std::runtime_error("Invalid objective for " + instance);

            results << instance << ",Greedy Edges Random," << run << ",-1," << objective << ',';
            for (std::size_t i = 0; i < solution.size(); ++i)
                results << (i == 0 ? "" : " ") << solution[i];
            results << '\n';
        }
        std::cout << instance << ": " << runs << " local optima" << std::endl;
    }
}
