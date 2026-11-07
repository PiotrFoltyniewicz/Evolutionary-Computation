#pragma once

#include "types.hpp"

// Alternative improving-move-list search from assignment 5, without candidates.
// Modifies the existing cycle and returns its final objective.
int moveListLocalSearch(const Nodes &nodes, Solution &solution);
