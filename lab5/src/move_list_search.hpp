#pragma once

#include "types.hpp"

// Alternative improving-move-list search from assignment 5, without candidates.
// Modifies the existing cycle and returns its final objective.
// Optionally accumulate the number of applied improving moves.
int moveListLocalSearch(const Nodes &nodes, Solution &solution,
                        int *improvingMoves = nullptr);
