#ifndef __GRID_MAP_H
#define __GRID_MAP_H

#include <jsoncpp/json/json.h>
#include <stdint.h>

struct Point2f {
    float x;
    float y;

    Point2f()
        : x(0), y(0) {}
    Point2f(float x, float y)
        : x(x), y(y) {}
};

struct Point2i {
    uint32_t x;
    uint32_t y;

    Point2i()
        : x(0), y(0) {}
    Point2i(uint32_t x, uint32_t y)
        : x(x), y(y) {}
};

class GridMap {
    public:
    GridMap(Json::Value info, Json::Value data, Json::Value header=Json::Value());

    uint32_t width() const;
    uint32_t height() const;

    float resolution() const;
    
    uint32_t getFromMetric(float x, float y) const;
    uint32_t getFromGrid(int x, int y) const;
    
    inline Point2i toGrid(float x, float y) const;
    inline Point2f toMetric(uint32_t x, uint32_t y) const;

    protected:
    Json::Value _info, _header, _data;
};

#endif