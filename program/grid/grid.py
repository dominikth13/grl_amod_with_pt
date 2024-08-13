from __future__ import annotations
import csv
from program.grid.grid_cell import GridCell
from program.location.location import Location
from program.zone.zone import Zone
from program.logger import LOGGER
from program.utils import IdProvider
from program.zone.zones import Zones


ID_PROVIDER = IdProvider()


class Grid:
    _grid = None

    def get_instance() -> Grid:
        if Grid._grid == None:
            Grid._grid = Grid()
        return Grid._grid

    def __init__(self):
        self.zones_dict: dict[int, Zone] = {zone.id: zone for zone in Zones.get_zones()}
        self.cells_dict: dict[int, list[GridCell]] = {
            zone_id: [] for zone_id in self.zones_dict.keys()
        }

        LOGGER.debug("Starting to create grid cells")
        cells_by_lat_long = {}

        with open("data/grid_cells.csv", mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                zone_id = int(float(row["zone_id"]))
                lat = float(row["lat"])
                long = float(row["long"])

                if lat not in cells_by_lat_long:
                    cells_by_lat_long[lat] = {}

                cells_by_lat_long[lat][long] = GridCell(
                    Location(lat, long), self.zones_dict[zone_id]
                )
                self.cells_dict[zone_id].append(cells_by_lat_long[lat][long])

        # cells is a two dimensional sorted array sorted by lat in the outer and long in the inner dimension
        self.cells: list[list[GridCell]] = [
            [None for _ in cells_by_lat_long[lat]] for lat in cells_by_lat_long
        ]
        self.cells_to_indices: dict[GridCell, tuple[int, int]] = {}
        sorted_lat = sorted(cells_by_lat_long)
        for i in range(len(sorted_lat)):
            sorted_long = sorted(cells_by_lat_long[sorted_lat[i]])
            for j in range(len(sorted_long)):
                self.cells[i][j] = cells_by_lat_long[sorted_lat[i]][sorted_long[j]]
                self.cells_to_indices[
                    cells_by_lat_long[sorted_lat[i]][sorted_long[j]]
                ] = (i, j)
        LOGGER.debug("Finished to create grid cells")

    # Find the fitting zone to a coordinate location
    def find_zone(self, location: Location) -> Zone:
        return self.find_cell(location).zone

    # Find the fitting cell to a coordinate location
    # Use two binary searches on lat and long to reduce runtime to O(log(sqrt(n)))
    def find_cell(self, location: Location) -> GridCell:
        low = 0
        high = len(self.cells) - 1
        mid = 0

        first_selection = []
        # Use binary search for lat
        while low <= high:
            mid = (high + low) // 2

            if mid == 0 or mid == len(self.cells) - 1:
                first_selection = self.cells[mid]
                break

            if self.cells[mid][0].center.lat < location.lat:
                if self.cells[mid + 1][0].center.lat >= location.lat:
                    first_selection = (
                        self.cells[mid]
                        if abs(self.cells[mid][0].center.lat - location.lat)
                        <= abs(self.cells[mid + 1][0].center.lat - location.lat)
                        else self.cells[mid + 1]
                    )
                    break
                else:
                    low = mid + 1
            else:
                if self.cells[mid - 1][0].center.lat <= location.lat:
                    first_selection = (
                        self.cells[mid]
                        if abs(self.cells[mid][0].center.lat - location.lat)
                        <= abs(self.cells[mid - 1][0].center.lat - location.lat)
                        else self.cells[mid - 1]
                    )
                    break
                else:
                    high = mid - 1

        if len(first_selection) == 0:
            raise Exception(f"Latitude {location.lat} not in range")

        low = 0
        high = len(first_selection) - 1
        mid = 0

        final_cell = None
        # Use binary search for lon
        while low <= high:
            mid = (high + low) // 2

            if mid == 0 or mid == len(first_selection) - 1:
                final_cell = first_selection[mid]
                break

            if first_selection[mid].center.lon < location.lon:
                if first_selection[mid + 1].center.lon >= location.lon:
                    if (
                        first_selection[mid].is_empty()
                        or first_selection[mid + 1].is_empty()
                    ):
                        final_cell = (
                            first_selection[mid]
                            if first_selection[mid + 1].is_empty()
                            else first_selection[mid + 1]
                        )
                        break
                    final_cell = (
                        first_selection[mid]
                        if abs(first_selection[mid].center.lon - location.lon)
                        <= abs(first_selection[mid + 1].center.lon - location.lon)
                        else first_selection[mid + 1]
                    )
                    break
                else:
                    low = mid + 1
            else:
                if first_selection[mid - 1].center.lon <= location.lon:
                    if (
                        first_selection[mid].is_empty()
                        or first_selection[mid - 1].is_empty()
                    ):
                        final_cell = (
                            first_selection[mid]
                            if first_selection[mid - 1].is_empty()
                            else first_selection[mid - 1]
                        )
                        break
                    final_cell = (
                        first_selection[mid]
                        if abs(first_selection[mid].center.lon - location.lon)
                        <= abs(first_selection[mid - 1].center.lon - location.lon)
                        else first_selection[mid - 1]
                    )
                    break
                else:
                    high = mid - 1

        if final_cell == None:
            raise Exception(f"Longitude {location.lon} not in range")

        return final_cell

    def find_n_adjacent_cells(self, cell: GridCell, n: int) -> set[GridCell]:
        cell_set = set()
        (i, j) = self.cells_to_indices[cell]
        min_i = i - n if i - n > 0 else 0
        max_i = i + n if i + n < len(self.cells) else len(self.cells) - 1
        min_j = j - n if j - n > 0 else 0
        max_j = j + n if j + n < len(self.cells[i]) else len(self.cells[i]) - 1

        for i in range(min_i, max_i + 1):
            for j in range(min_j, max_j + 1):
                cell_set.add(self.cells[i][j])
        return cell_set
