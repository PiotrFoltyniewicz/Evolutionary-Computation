#pragma once

#include "types.hpp"
#include "experiment.hpp"
#include <random>

enum class SearchType { Steepest, Greedy };
enum class IntraRouteMove { NodesExchange, EdgesExchange };

// Both methods modify an existing solution and return its final objective.
// Every iteration considers inter-route exchange AND the chosen intra-route moves.
int steepestLocalSearch(const Nodes &nodes, Solution &solution, IntraRouteMove intraMove);
int greedyLocalSearch(const Nodes &nodes, Solution &solution, IntraRouteMove intraMove);
int localSearch(const Nodes &nodes, Solution &solution, SearchType search,
                IntraRouteMove intraMove);

enum class StartingSolutionType { Random, Greedy };

// Construction is injected so the best lab1/lab2 heuristic can be selected per instance.
int createStartingSolution(const Nodes &nodes, int startNode, Solution &solution,
                           StartingSolutionType type, const Algorithm &greedyConstructor);
