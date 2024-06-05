from __future__ import annotations

from program.grid.grid import Grid
from params.program_params import ProgramParams
from program.public_transport.station import Station
from program.location.location import Location
from program.order.order import Order
from program.utils import IdProvider

ID_PROVIDER = IdProvider()

# Class route contains data model of route object
class Route:
    def __init__(
        self,
        order: Order,
        origin: Location,
        destination: Location,
        stations: list[Station],
        vehicle_time: float,
        transit_time: float,
        walking_time: float,
        other_time: float,
        total_time: float,
    ) -> None:
        self.id = ID_PROVIDER.get_uuid()
        self.order = order
        self.origin = origin
        self.destination = destination
        self.stations = stations
        self.transit_time = transit_time
        self.walking_time = walking_time
        self.other_time = other_time
        self.total_time = total_time
        self.vehicle_time = vehicle_time
        self.vehicle_destination = destination if stations == [] else stations[0].position
        self.vehicle_destination_cell = (
            Grid.get_instance().find_cell(
                destination if stations == [] else stations[0].position
            )
        )
        # How many seconds the route saves for the customer
        self.time_reduction = order.direct_connection[1] - total_time

    def is_regular_route(self) -> bool:
        return self.stations == []

    def regular_route(order: Order) -> Route:
        distance_in_m = order.start.distance_to(order.end)
        vehicle_time = distance_in_m / ProgramParams.VEHICLE_SPEED

        return Route(
            order,
            order.start,
            order.end,
            [],
            vehicle_time,
            0,
            0,
            0,
            vehicle_time,
        )
