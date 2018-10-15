#include <limits>
#include "benchbot/grid_map.hpp"

GridMap::GridMap(Json::Value info, Json::Value data, Json::Value header)
    : _info(info), _data(data), _header(header) {
}

inline uint32_t GridMap::width() const {
    return _info["width"].asUInt();
}
inline uint32_t GridMap::height() const {
    return _info["height"].asUInt();
}

inline float GridMap::resolution() const {
    return _info["resolution"].asFloat();
}

uint32_t GridMap::getFromMetric(float x, float y) const {
    Point2i point = toGrid(x, y);
    return getFromGrid(point.x, point.y);
}
uint32_t GridMap::getFromGrid(int x, int y) const {
    if (0 > x >= width()) {
        return std::numeric_limits<uint32_t>::max();
    }
    if (0 > y >= height()) {
        return std::numeric_limits<uint32_t>::max();
    }
        
    int index = width() * y + x;
    
    if (_data.size() <= index) {
        return std::numeric_limits<uint32_t>::max();
    }
        
    return _data[index].asInt();
}

inline Point2i GridMap::toGrid(float x, float y) const {
    return Point2i(
        (int)(x / resolution()),
        (int)(y / resolution())
    );
}
inline Point2f GridMap::toMetric(uint32_t x, uint32_t y) const {
    return Point2f(
        x * resolution(),
        y * resolution()
    );
}