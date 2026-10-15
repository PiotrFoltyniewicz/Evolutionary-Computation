#include "data_reader.hpp"

#include <fstream>

void readFile(const char *filename, Nodes &nodesArr)
{
    std::ifstream stream(filename);

    if (!stream)
        throw std::runtime_error("File openning error");

    int x;
    int y;
    int cost;

    char del1;
    char del2;

    int i = 0;
    while (stream >> x >> del1 >> y >> del2 >> cost)
    {
        Node node{x, y, cost};
        nodesArr[i++] = node;
    }
}

void calculateDistances(Nodes &nodesArr)
{
    for (std::size_t i = 0; i < nodesArr.size(); ++i)
    {
        for (std::size_t j = i + 1; j < nodesArr.size(); ++j)
        {
            Node &tmp1 = nodesArr[i];
            Node &tmp2 = nodesArr[j];
            int distance = round(std::hypot(tmp1.x - tmp2.x, tmp1.y - tmp2.y));

            tmp1.distances[j] = distance;
            tmp2.distances[i] = distance;
        }
    }
}
