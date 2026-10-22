#pragma once

#include "local_search_methods.hpp"
#include <array>
#include <ostream>
#include <string>

struct LocalSearchVariant
{
    const char *name;
    SearchType search;
    IntraRouteMove intraMove;
    StartingSolutionType start;
};

inline constexpr std::array<LocalSearchVariant, 8> LOCAL_SEARCH_VARIANTS{{{"Steepest Nodes Random", SearchType::Steepest, IntraRouteMove::NodesExchange, StartingSolutionType::Random},
                                                                          {"Steepest Nodes Greedy", SearchType::Steepest, IntraRouteMove::NodesExchange, StartingSolutionType::Greedy},
                                                                          {"Steepest Edges Random", SearchType::Steepest, IntraRouteMove::EdgesExchange, StartingSolutionType::Random},
                                                                          {"Steepest Edges Greedy", SearchType::Steepest, IntraRouteMove::EdgesExchange, StartingSolutionType::Greedy},
                                                                          {"Greedy Nodes Random", SearchType::Greedy, IntraRouteMove::NodesExchange, StartingSolutionType::Random},
                                                                          {"Greedy Nodes Greedy", SearchType::Greedy, IntraRouteMove::NodesExchange, StartingSolutionType::Greedy},
                                                                          {"Greedy Edges Random", SearchType::Greedy, IntraRouteMove::EdgesExchange, StartingSolutionType::Random},
                                                                          {"Greedy Edges Greedy", SearchType::Greedy, IntraRouteMove::EdgesExchange, StartingSolutionType::Greedy}}};

// Adapter matching common/src/experiment.hpp's Algorithm signature.
int runLocalSearchVariant(const Nodes &nodes, int startNode, Solution &solution,
                          const LocalSearchVariant &variant,
                          const Algorithm &greedyConstructor);

void runExperimentForFile(const std::string &filename, std::ostream &results,
                          std::ostream &summary);
