#pragma once

#include "types.hpp"

#include <functional>
#include <limits>
#include <ostream>

using Algorithm = std::function<int(const Nodes &, int, Solution &)>;

struct ExperimentStats
{
    int minValue = std::numeric_limits<int>::max();
    int maxValue = std::numeric_limits<int>::min();
    double average = 0.0;
    double averageTimeMs = 0.0;
};

ExperimentStats runExperiment(const Nodes &nodes, const Algorithm &algorithm,
                             const std::string &instance, const std::string &method,
                             std::ostream &results, bool usesStartNode = true);
