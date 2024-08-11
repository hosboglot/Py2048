#include "tile.h"

Tile::Tile(QObject *parent)
    : m_value(2),
    QObject{parent}
{}

int Tile::value() const
{
    return m_value;
}

void Tile::setValue(const int &v)
{
    if (m_value != v){
        m_value = v;
        emit valueChanged(v);
    }
}
