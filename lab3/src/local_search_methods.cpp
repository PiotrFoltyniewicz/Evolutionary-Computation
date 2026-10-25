#include "local_search_methods.hpp"

#include <algorithm>
#include <array>
#include <numeric>
#include <stdexcept>
#include <vector>

namespace
{
    enum class MoveType
    {
        InterRouteExchange,
        IntraRouteNodesExchange,
        IntraRouteEdgesExchange
    };

    // Descriptors only: no neighbor solutions or precomputed deltas.
    struct Move
    {
        MoveType type;
        int firstPosition;
        int secondPosition = -1; // Intra-route only; edge moves use edge start positions.
        int incomingNode = -1;   // Inter-route only; ID of the unselected node.
    };

    std::vector<Move> generateMoves(const Solution &solution, IntraRouteMove intraMove)
    {
        const int size = static_cast<int>(solution.size());
        std::array<bool, PROBLEMSIZE> selected{};
        for (const int node : solution)
            selected[node] = true;

        std::vector<Move> moves;
        moves.reserve(size * (PROBLEMSIZE - size) + size * (size - 1) / 2);
        for (int position = 0; position < size; ++position)
        {
            for (int node = 0; node < PROBLEMSIZE; ++node)
            {
                if (!selected[node])
                    moves.push_back({MoveType::InterRouteExchange, position, -1, node});
            }
        }

        for (int first = 0; first < size; ++first)
        {
            for (int second = first + 1; second < size; ++second)
            {
                if (intraMove == IntraRouteMove::NodesExchange)
                {
                    moves.push_back({MoveType::IntraRouteNodesExchange, first, second});
                }
                else
                {
                    const bool adjacentEdges = second == first + 1 ||
                                               (first == 0 && second == size - 1);
                    if (!adjacentEdges)
                        moves.push_back({MoveType::IntraRouteEdgesExchange, first, second});
                }
            }
        }
        return moves;
    }

    int interRouteExchangeDelta(const Nodes &nodes, const Solution &solution,
                                int position, int incomingNode)
    {
        const int size = static_cast<int>(solution.size());
        const int outgoing = solution[position];
        const int previous = solution[(position + size - 1) % size];
        const int next = solution[(position + 1) % size];
        return nodes[previous].distances[incomingNode] + nodes[incomingNode].distances[next] - nodes[previous].distances[outgoing] - nodes[outgoing].distances[next] + nodes[incomingNode].cost - nodes[outgoing].cost;
    }

    int nodesExchangeDelta(const Nodes &nodes, const Solution &solution, int first, int second)
    {
        const int size = static_cast<int>(solution.size());
        // Only these four directed edges can change. Deduplicate their starting
        // positions to handle adjacent nodes, including the closing edge.
        std::array<int, 4> affectedEdgePositions{(first + size - 1) % size, first,
                                                 (second + size - 1) % size, second};
        std::sort(affectedEdgePositions.begin(), affectedEdgePositions.end());
        const auto uniqueEnd = std::unique(affectedEdgePositions.begin(), affectedEdgePositions.end());
        const auto nodeAfterSwap = [&](int position)
        {
            if (position == first)
                return solution[second];
            if (position == second)
                return solution[first];
            return solution[position];
        };
        int delta = 0;
        for (auto edge = affectedEdgePositions.begin(); edge != uniqueEnd; ++edge)
        {
            const int next = (*edge + 1) % size;
            delta += nodes[nodeAfterSwap(*edge)].distances[nodeAfterSwap(next)] - nodes[solution[*edge]].distances[solution[next]];
        }
        return delta;
    }

    int edgesExchangeDelta(const Nodes &nodes, const Solution &solution, int first, int second)
    {
        // Distances are symmetric, so reversing internal edges does not change cost.
        const int size = static_cast<int>(solution.size());
        const int a = solution[first];
        const int b = solution[(first + 1) % size];
        const int c = solution[second];
        const int d = solution[(second + 1) % size];
        // Remove (a, b) and (c, d); add (a, c) and (b, d).
        return nodes[a].distances[c] + nodes[b].distances[d] - nodes[a].distances[b] - nodes[c].distances[d];
    }

    int evaluateMoveDelta(const Nodes &nodes, const Solution &solution, const Move &move)
    {
        switch (move.type)
        {
        case MoveType::InterRouteExchange:
            return interRouteExchangeDelta(nodes, solution, move.firstPosition, move.incomingNode);
        case MoveType::IntraRouteNodesExchange:
            return nodesExchangeDelta(nodes, solution, move.firstPosition, move.secondPosition);
        case MoveType::IntraRouteEdgesExchange:
            return edgesExchangeDelta(nodes, solution, move.firstPosition, move.secondPosition);
        }
        throw std::runtime_error("Invalid MoveType");
    }

    void applyMove(Solution &solution, const Move &move)
    {
        switch (move.type)
        {
        case MoveType::InterRouteExchange:
            solution[move.firstPosition] = move.incomingNode;
            return;
        case MoveType::IntraRouteNodesExchange:
            std::swap(solution[move.firstPosition], solution[move.secondPosition]);
            return;
        case MoveType::IntraRouteEdgesExchange:
        {
            const int first = std::min(move.firstPosition, move.secondPosition);
            const int second = std::max(move.firstPosition, move.secondPosition);
            std::reverse(solution.begin() + first + 1, solution.begin() + second + 1);
            return;
        }
        }
    }
}

int steepestLocalSearch(const Nodes &nodes, Solution &solution, IntraRouteMove intraMove)
{
    int objective = assessSolution(nodes, solution);

    while (true)
    {
        const auto moves = generateMoves(solution, intraMove);
        int bestDelta = 0;
        Move bestMove{};
        for (const auto &move : moves)
        {
            const int delta = evaluateMoveDelta(nodes, solution, move);
            if (delta < bestDelta)
            {
                bestDelta = delta;
                bestMove = move;
            }
        }
        if (bestDelta == 0)
            return objective;
        applyMove(solution, bestMove);
        objective += bestDelta;
    }
}

int greedyLocalSearch(const Nodes &nodes, Solution &solution, IntraRouteMove intraMove)
{
    int objective = assessSolution(nodes, solution);

    std::random_device rd;
    std::mt19937 gen(rd());

    while (true)
    {
        auto moves = generateMoves(solution, intraMove);

        std::shuffle(moves.begin(), moves.end(), gen);
        bool improved = false;
        for (const auto &move : moves)
        {
            const int delta = evaluateMoveDelta(nodes, solution, move);
            if (delta < 0)
            {
                applyMove(solution, move);
                objective += delta;
                improved = true;
                break;
            }
        }
        if (!improved)
            return objective;
    }
}

int localSearch(const Nodes &nodes, Solution &solution, SearchType search,
                IntraRouteMove intraMove)
{
    switch (search)
    {
    case SearchType::Steepest:
        return steepestLocalSearch(nodes, solution, intraMove);
    case SearchType::Greedy:
        return greedyLocalSearch(nodes, solution, intraMove);
    }
}

int createStartingSolution(const Nodes &nodes, int startNode, Solution &solution,
                           StartingSolutionType type, const Algorithm &greedyConstructor)
{
    switch (type)
    {
    case StartingSolutionType::Random:
    {
        std::random_device rd;
        std::mt19937 gen(rd());

        solution.resize(PROBLEMSIZE);
        std::iota(solution.begin(), solution.end(), 0);
        std::shuffle(solution.begin(), solution.end(), gen);
        solution.resize(SOLUTIONSIZE);
        return assessSolution(nodes, solution);
    }
    case StartingSolutionType::Greedy:
        solution.clear();
        return greedyConstructor(nodes, startNode, solution);
    }
    throw std::invalid_argument("Unknown starting solution type");
}
