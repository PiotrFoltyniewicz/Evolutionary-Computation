#pragma once

#include <ostream>
#include <string>

namespace lab6
{
    void runExperimentForFile(const std::string &filename, int instanceIndex,
                              std::ostream &results, std::ostream &summary);
}
