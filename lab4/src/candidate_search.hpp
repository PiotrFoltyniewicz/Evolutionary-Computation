#pragma once

#include "types.hpp"

#include <array>
#include <compare>
#include <variant>
#include <vector>

// An undirected edge {u, v} is a candidate if either endpoint places the other
// in its k nearest list, ranked by distance(u, v) + cost[v]. Lists store this union.
using CandidateLists = std::array<std::vector<int>, PROBLEMSIZE>;

struct InterRouteExchange
{
    int firstPosition;
    int incomingNode;

    auto operator<=>(const InterRouteExchange &) const = default;
};

struct IntraRouteEdgesExchange
{
    int firstPosition;
    int secondPosition;

    auto operator<=>(const IntraRouteEdgesExchange &) const = default;
};

using Move = std::variant<InterRouteExchange, IntraRouteEdgesExchange>;

CandidateLists buildCandidateLists(const Nodes &nodes, int k = 10);

std::vector<Move> generateMoves(const Solution &solution, const CandidateLists &candidates);
int evaluateMoveDelta(const Nodes &nodes, const Solution &solution, const Move &move);
void applyMove(Solution &solution, const Move &move);
int steepestLocalSearch(const Nodes &nodes, Solution &solution, const CandidateLists &candidates);
