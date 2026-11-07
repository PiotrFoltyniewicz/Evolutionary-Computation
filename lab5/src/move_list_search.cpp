#include "move_list_search.hpp"

#include <algorithm>
#include <array>
#include <queue>
#include <tuple>
#include <vector>

namespace
{
    enum class MoveType
    {
        InterRouteExchange,
        IntraRouteEdgesExchange
    };
    enum class MoveStatus
    {
        Invalid,
        Deferred,
        Applicable
    };
    enum class EdgeDirection
    {
        Missing,
        Forward,
        Reversed
    };

    // Store node IDs, never positions: reversals can change every position.
    // Inter: replace b by d, with neighbors a and c.
    // Edges: remove (a,b),(c,d), add (a,c),(b,d).
    struct Move
    {
        int delta;
        MoveType type;
        int a, b, c, d;
    };

    struct WorseMove
    {
        bool operator()(const Move &left, const Move &right) const
        {
            return std::tie(left.delta, left.type, left.a, left.b, left.c, left.d) >
                   std::tie(right.delta, right.type, right.a, right.b, right.c, right.d);
        }
    };

    using MoveList = std::priority_queue<Move, std::vector<Move>, WorseMove>;
    using Positions = std::array<int, PROBLEMSIZE>;

    Positions positionsOf(const Solution &solution)
    {
        Positions positions;
        positions.fill(-1);
        for (int i = 0; i < static_cast<int>(solution.size()); ++i)
            positions[solution[i]] = i;
        return positions;
    }

    // Direction relative to the saved edge (a, b).
    EdgeDirection edgeDirection(const Solution &solution, const Positions &positions, int a, int b)
    {
        if (positions[a] < 0 || positions[b] < 0)
            return EdgeDirection::Missing;
        const int size = static_cast<int>(solution.size());
        if (solution[(positions[a] + 1) % size] == b)
            return EdgeDirection::Forward;
        if (solution[(positions[b] + 1) % size] == a)
            return EdgeDirection::Reversed;
        return EdgeDirection::Missing;
    }

    MoveStatus moveStatus(const Solution &solution, const Positions &positions, const Move &move)
    {
        if (move.type == MoveType::InterRouteExchange)
        {
            // The cached delta is valid only with the same two neighbors
            // (in either order), and while the incoming node is unselected.
            if (positions[move.d] >= 0 || positions[move.b] < 0)
                return MoveStatus::Invalid;
            return edgeDirection(solution, positions, move.a, move.b) != EdgeDirection::Missing &&
                           edgeDirection(solution, positions, move.b, move.c) != EdgeDirection::Missing
                       ? MoveStatus::Applicable
                       : MoveStatus::Invalid;
        }
        const EdgeDirection first = edgeDirection(solution, positions, move.a, move.b);
        const EdgeDirection second = edgeDirection(solution, positions, move.c, move.d);
        if (first == EdgeDirection::Missing || second == EdgeDirection::Missing)
            return MoveStatus::Invalid;
        return first == second ? MoveStatus::Applicable : MoveStatus::Deferred;
    }

    MoveList generateImprovingMoves(const Nodes &nodes, const Solution &solution,
                                    const Positions &positions)
    {
        const int size = static_cast<int>(solution.size());
        std::vector<Move> moves;
        moves.reserve(size * (PROBLEMSIZE - size) + size * (size - 3));
        for (int i = 0; i < size; ++i)
        {
            const int a = solution[(i + size - 1) % size];
            const int b = solution[i];
            const int c = solution[(i + 1) % size];
            for (int d = 0; d < PROBLEMSIZE; ++d)
            {
                if (positions[d] >= 0)
                    continue;
                const int delta = nodes[a].distances[d] + nodes[d].distances[c] -
                                  nodes[a].distances[b] - nodes[b].distances[c] +
                                  nodes[d].cost - nodes[b].cost;
                if (delta < 0)
                    moves.push_back({delta, MoveType::InterRouteExchange, a, b, c, d});
            }
        }
        for (int i = 0; i < size; ++i)
        {
            for (int j = i + 2; j < size; ++j)
            {
                if (i == 0 && j == size - 1)
                    continue; // Nonadjacent edges only, including the closing edge.
                const int a = solution[i];
                const int b = solution[(i + 1) % size];
                const int c = solution[j];
                const int d = solution[(j + 1) % size];
                const int removed = nodes[a].distances[b] + nodes[c].distances[d];
                const int delta = nodes[a].distances[c] + nodes[b].distances[d] - removed;
                if (delta < 0)
                    moves.push_back({delta, MoveType::IntraRouteEdgesExchange, a, b, c, d});
                // Also save the other relative orientation, initially deferred.
                const int invertedDelta = nodes[a].distances[d] + nodes[b].distances[c] - removed;
                if (invertedDelta < 0)
                    moves.push_back({invertedDelta, MoveType::IntraRouteEdgesExchange, a, b, d, c});
            }
        }
        return MoveList(WorseMove{}, std::move(moves));
    }

    void applyMove(Solution &solution, const Positions &positions, const Move &move)
    {
        if (move.type == MoveType::InterRouteExchange)
        {
            solution[positions[move.b]] = move.d;
            return;
        }
        const bool forward = edgeDirection(solution, positions, move.a, move.b) == EdgeDirection::Forward;
        int first = positions[forward ? move.a : move.b];
        int second = positions[forward ? move.c : move.d];
        if (first > second)
            std::swap(first, second);
        std::reverse(solution.begin() + first + 1, solution.begin() + second + 1);
    }

    bool takeApplicableMove(MoveList &moves, const Solution &solution,
                            const Positions &positions, Move &chosen)
    {
        std::vector<Move> deferred;
        bool found = false;
        while (!moves.empty())
        {
            const Move move = moves.top();
            moves.pop();
            const auto status = moveStatus(solution, positions, move);
            if (status == MoveStatus::Applicable)
            {
                chosen = move;
                found = true;
                break;
            }
            if (status == MoveStatus::Deferred)
                deferred.push_back(move);
            // Invalid descriptors are discarded permanently.
        }
        for (const auto &move : deferred)
            moves.push(move);
        return found;
    }
}

int moveListLocalSearch(const Nodes &nodes, Solution &solution)
{
    int objective = assessSolution(nodes, solution);
    auto positions = positionsOf(solution);
    auto moves = generateImprovingMoves(nodes, solution, positions);
    while (true)
    {
        Move chosen{};
        if (!takeApplicableMove(moves, solution, positions, chosen))
        {
            // Alternative algorithm: refresh only after exhausting applicable
            // saved moves. Rebuilding also deduplicates retained deferred moves:
            // both orientations of every surviving edge pair are generated again.
            moves = generateImprovingMoves(nodes, solution, positions);
            if (!takeApplicableMove(moves, solution, positions, chosen))
                return objective; // Deferred-only LM cannot improve this cycle.
        }
        applyMove(solution, positions, chosen);
        objective += chosen.delta;
        positions = positionsOf(solution);
    }
}
