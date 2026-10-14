#pragma once

#include <functional>
#include <limits>
#include <string>
#include <vector>

#include "types.hpp"

struct ExperimentStats
{
    int minValue = std::numeric_limits<int>::max();
    int maxValue = std::numeric_limits<int>::min();
    double average = 0.0;
    double averageTimeMs = 0.0;
};

ExperimentStats statsForValues(const std::vector<int> &values);
ExperimentStats runStartNodeExperiment(const Nodes &nodes, std::function<int(const Nodes &, int, Solution &)> algorithm);
ExperimentStats runRandomExperiment(const Nodes &nodes, int samples);
void printExperimentSummary(const std::string &label, const ExperimentStats &stats);
