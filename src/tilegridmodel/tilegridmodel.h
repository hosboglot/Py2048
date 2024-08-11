#ifndef TILEGRIDMODEL_H
#define TILEGRIDMODEL_H

#include <QAbstractTableModel>
#include <QList>

#include "tile.h"

using TileGrid = QList<QList<Tile*>>;

class TileGridModel : public QAbstractTableModel
{
    Q_OBJECT

public:
    explicit TileGridModel(int row_count, int column_count, QObject *parent = nullptr);

    // Basic functionality:
    int rowCount(const QModelIndex &parent = QModelIndex()) const override;
    int columnCount(const QModelIndex &parent = QModelIndex()) const override;

    QVariant data(const QModelIndex &index, int role = Qt::DisplayRole) const override;

    // Editable:
    bool setData(const QModelIndex &index, const QVariant &value, int role = Qt::EditRole) override;

    Qt::ItemFlags flags(const QModelIndex &index) const override;

private:
    TileGrid m_tilegrid;
};

#endif // TILEGRIDMODEL_H
