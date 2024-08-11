#ifndef TILE_H
#define TILE_H

#include <QObject>

class Tile : public QObject
{
    Q_OBJECT
    Q_PROPERTY(int value READ value WRITE setValue NOTIFY valueChanged)

public:
    explicit Tile(QObject *parent = nullptr);

    int value() const;
    void setValue(const int& v);
signals:
    void valueChanged(int);
private:
    int m_value;
};

#endif // TILE_H
