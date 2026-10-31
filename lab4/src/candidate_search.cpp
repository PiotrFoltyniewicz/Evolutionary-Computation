#include "candidate_search.hpp"

#include <algorithm>

CandidateLists buildCandidateLists(const Nodes &nodes, int k)
{
    std::array<std::array<bool, PROBLEMSIZE>, PROBLEMSIZE> adjacent{};
    for (int u = 0; u < PROBLEMSIZE; ++u)
    {
        std::vector<int> nearest;
        nearest.reserve(PROBLEMSIZE - 1);
        for (int v = 0; v < PROBLEMSIZE; ++v)
            if (v != u)
                nearest.push_back(v);
        std::partial_sort(nearest.begin(), nearest.begin() + k, nearest.end(),
                          [&](int a, int b) {
            return std::pair{nodes[u].distances[a] + nodes[a].cost, a} <
                   std::pair{nodes[u].distances[b] + nodes[b].cost, b};
        });
        for (int i = 0; i < k; ++i)
            adjacent[u][nearest[i]] = adjacent[nearest[i]][u] = true;
    }

    CandidateLists candidates;
    for (int u = 0; u < PROBLEMSIZE; ++u)
        for (int v = 0; v < PROBLEMSIZE; ++v)
            if (adjacent[u][v])
                candidates[u].push_back(v);
    return candidates;
}

std::vector<Move> generateMoves(const Solution &solution, const CandidateLists &candidates)
{
    const int size = SOLUTIONSIZE;
    std::array<int, PROBLEMSIZE> position;
    position.fill(-1);
    std::size_t incidentEdges = 0;
    for (int i = 0; i < size; ++i)
    {
        position[solution[i]] = i;
        incidentEdges += candidates[solution[i]].size();
    }

    std::vector<Move> moves;
    moves.reserve(2 * incidentEdges);
    const auto addEdgesExchange = [&](int firstPosition, int secondPosition) {
        if (firstPosition > secondPosition)
            std::swap(firstPosition, secondPosition);
        if (secondPosition == firstPosition || secondPosition == firstPosition + 1 ||
            (firstPosition == 0 && secondPosition == size - 1))
            return; // Shared cut endpoint: does not introduce the candidate edge.
        moves.push_back(IntraRouteEdgesExchange{firstPosition, secondPosition});
    };

    for (int i = 0; i < size; ++i)
    {
        const int u = solution[i];
        for (const int v : candidates[u])
        {
            const int j = position[v];
            if (j == -1)
            {
                // Keep u and replace either neighbor of u by v, adding {u, v}.
                moves.push_back(InterRouteExchange{(i + size - 1) % size, v});
                moves.push_back(InterRouteExchange{(i + 1) % size, v});
            }
            else if (u < v)
            {
                // Cut after both endpoints, or before both endpoints.
                addEdgesExchange(i, j);
                addEdgesExchange((i + size - 1) % size, (j + size - 1) % size);
            }
        }
    }
    return moves;
}

int evaluateMoveDelta(const Nodes &nodes, const Solution &solution, const Move &move)
{
    const int size = SOLUTIONSIZE;
    if (const auto *exchange = std::get_if<InterRouteExchange>(&move))
    {
        const int outgoing = solution[exchange->firstPosition];
        const int previous = solution[(exchange->firstPosition + size - 1) % size];
        const int next = solution[(exchange->firstPosition + 1) % size];
        const int incoming = exchange->incomingNode;
        return nodes[previous].distances[incoming] + nodes[incoming].distances[next] -
               nodes[previous].distances[outgoing] - nodes[outgoing].distances[next] +
               nodes[incoming].cost - nodes[outgoing].cost;
    }
    const auto &exchange = std::get<IntraRouteEdgesExchange>(move);
    const int a = solution[exchange.firstPosition];
    const int b = solution[(exchange.firstPosition + 1) % size];
    const int c = solution[exchange.secondPosition];
    const int d = solution[(exchange.secondPosition + 1) % size];
    return nodes[a].distances[c] + nodes[b].distances[d] -
           nodes[a].distances[b] - nodes[c].distances[d];
}

void applyMove(Solution &solution, const Move &move)
{
    if (const auto *exchange = std::get_if<InterRouteExchange>(&move))
        solution[exchange->firstPosition] = exchange->incomingNode;
    else
    {
        const auto &edgesExchange = std::get<IntraRouteEdgesExchange>(move);
        std::reverse(solution.begin() + edgesExchange.firstPosition + 1,
                     solution.begin() + edgesExchange.secondPosition + 1);
    }
}

int steepestLocalSearch(const Nodes &nodes, Solution &solution, const CandidateLists &candidates)
{
    int objective = assessSolution(nodes, solution);
    while (true)
    {
        int bestDelta = 0;
        Move bestMove{};
        for (const auto &move : generateMoves(solution, candidates))
        {
            const int delta = evaluateMoveDelta(nodes, solution, move);
            if (delta < bestDelta ||
                (delta < 0 && delta == bestDelta && move < bestMove))
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
