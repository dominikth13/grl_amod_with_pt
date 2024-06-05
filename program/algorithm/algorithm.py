from multiprocessing import Manager, Pool
import time
from params.concurrency_params import ConcurrencyParams
from program.action.vehicle_action_pair import VehicleActionPair
from program.algorithm.model_builder import or_tools_min_cost_flow
from program.concurrency.helper_functions import generate_route_managed
from program.data_collector import DataCollector
from program.vehicle.vehicles import Vehicles
from program.grid.grid import Grid
from program.interval.time_series import TimeSeries
from program.logger import LOGGER
from params.program_params import Mode, ProgramParams
from program.public_transport.fastest_station_connection_network import (
    FastestStationConnectionNetwork,
)
from program.action.action import Action
from program.vehicle.vehicle import Vehicle
from program.order.order import Order
from program.order.route import Route
from program.state.state import State
from program.state.state_value_networks import StateValueNetworks


# The so called 'Algorithm 1' of Feng et al. (2022)
def generate_routes(orders: list[Order]) -> dict[Order, list[Route]]:
    routes_per_order = {order: [] for order in orders}
    fastest_connection_network = FastestStationConnectionNetwork.get_instance()
    start = time.time()
    if ConcurrencyParams.FEATURE_ROUTE_CALCULATION_CONCURRENT:
        with Pool(processes=ConcurrencyParams.AMOUNT_OF_PROCESSES) as pool:  # adjust the amount of processes to available cores
            results = pool.map(generate_routes_for, orders)
    else:
        results = []
        for order in orders:
            results.append(generate_routes_for(order))
    routes_per_order = {order: routes for order, routes in results}
    end = time.time()
    LOGGER.debug(
        f"The route generation took {round((end - start)*1000,4)} ms.")
    return routes_per_order

def generate_routes_for(order: Order) -> tuple[Order, list[Route]]:
    routes = []
    fastest_connection_network = FastestStationConnectionNetwork.get_instance()
    default_route = Route.regular_route(order)
    routes.append(default_route)
    start = order.start
    end = order.end

    if order.direct_connection[1] > ProgramParams.L1:
        # 1. Get the closest start and end station for each line
        from program.public_transport.station import Station

        origins: list[Station] = []
        destinations: list[Station] = []
        for line in fastest_connection_network.lines:
            origins.append(line.get_closest_station(start))
            destinations.append(line.get_closest_station(end))

        # 2. Generate combination routes
        for origin in origins:
            for destination in destinations:
                if origin == destination:
                    continue
                connection = fastest_connection_network.get_fastest_connection(
                    origin, destination
                )

                # Distance (time in second)
                vehicle_time = (
                    start.distance_to(origin.position) / ProgramParams.VEHICLE_SPEED
                )
                walking_time = (
                    destination.position.distance_to(end)
                    / ProgramParams.WALKING_SPEED
                )
                transit_time = connection[1]
                stations = connection[0]
                # include entry, exit and waiting time
                other_time = (
                    2 * ProgramParams.PUBLIC_TRANSPORT_ENTRY_EXIT_TIME
                    + ProgramParams.PUBLIC_TRANSPORT_WAITING_TIME(
                        order.dispatch_time
                    )
                )
                total_time = vehicle_time + walking_time + transit_time + other_time

                # Since we want people to use public transport, here we check against the direct_connection without any bus
                if total_time < order.direct_connection[1] + ProgramParams.L2:
                    routes.append(
                        Route(
                            order,
                            start,
                            end,
                            stations,
                            vehicle_time,
                            transit_time,
                            walking_time,
                            other_time,
                            total_time,
                        )
                    )
    return order, routes

def generate_vehicle_action_pairs(
    order_routes_dict: dict[Order, list[Route]]
) -> list[VehicleActionPair]:
    vehicle_to_idling_dict: dict[Vehicle, VehicleActionPair] = {}

    available_vehicles = list(
        filter(lambda x: not x.is_occupied(), Vehicles.get_vehicles())
    )

    # Central idling action
    idling = Action(None)

    # 1. Generate VehicleIdlingPair for each vehicle available
    for vehicle in available_vehicles:
        reward = (-1) * ProgramParams.IDLING_COST

        if ProgramParams.EXECUTION_MODE == Mode.GRAPH_REINFORCEMENT_LEARNING:
            state_value = StateValueNetworks.get_instance().get_target_state_value(
                idling,
                Grid.get_instance().find_zone(vehicle.current_position),
                State.get_state().current_time.add_seconds(
                    ProgramParams.SIMULATION_UPDATE_RATE
                ),
            )
        else:
            state_value = 0

        weight = reward + state_value
        vehicle_to_idling_dict[vehicle] = VehicleActionPair(vehicle, idling, weight)

    order_to_actions_dict: dict[Order, list[Action]] = {}
    # 2. Generate Actions for each route
    for order in order_routes_dict:
        order_to_actions_dict[order] = []
        for route in order_routes_dict[order]:
            order_to_actions_dict[order].append(Action(route))

    operated_orders = set()
    vehicle_to_orders_dict: dict[Vehicle, list[Order]] = {}
    # 3. Generate vehicle-order pairs for each vehicle available
    for vehicle in available_vehicles:
        vehicle_to_orders_dict[vehicle] = []
        for order in order_to_actions_dict:
            if (
                order.start.distance_to(vehicle.current_position)
                <= ProgramParams.PICK_UP_DISTANCE_THRESHOLD
            ):
                operated_orders.add(order)
                vehicle_to_orders_dict[vehicle].append(order)

    best_actions: dict[Order, tuple[Action, float]] = {}
    # 4. Calculate the actions Q-value for each route that maybe operated and save the best action
    for order in operated_orders:
        actions: list[tuple[Action, float]] = []
        # Calculate Q-values for all actions
        for action in order_to_actions_dict[order]:
            # For the Q-value calculation we expect the medium pickup distance threshold driving time
            arrival_time = State.get_state().current_time.add_seconds(
                ProgramParams.PICK_UP_DISTANCE_THRESHOLD
                / ProgramParams.VEHICLE_SPEED
                / 2
            ).add_seconds(action.route.vehicle_time)
            # weight = time reduction for passenger + state value after this option
            if ProgramParams.EXECUTION_MODE == Mode.GRAPH_REINFORCEMENT_LEARNING:
                state_value = StateValueNetworks.get_instance().get_target_state_value(
                    action,
                    action.route.vehicle_destination_cell.zone,
                    arrival_time,
                )
            else:
                # Baseline Performance
                state_value = 0

            weight = (
                action.route.time_reduction
                + ProgramParams.DISCOUNT_FACTOR(
                    State.get_state().current_time.distance_to(arrival_time)
                )
                * state_value
            )
            if action.route.is_regular_route():
                weight = weight * ProgramParams.DIRECT_TRIP_DISCOUNT_FACTOR
            actions.append((action, weight))

        # Save best action
        best_action = actions[0]
        for tup in actions:
            if best_action[1] < tup[1]:
                best_action = tup

        best_actions[order] = best_action

    vehicle_action_pairs = []
    # 5. Create VehicleRoutePairs and put them together with idling in return list
    for vehicle in vehicle_to_orders_dict:
        vehicle_action_pairs.append(vehicle_to_idling_dict[vehicle])

        for order in vehicle_to_orders_dict[vehicle]:
            vehicle_action_pairs.append(
                VehicleActionPair(
                    vehicle, best_actions[order][0], best_actions[order][1]
                )
            )

    return vehicle_action_pairs


def solve_optimization_problem(
    vehicle_action_pairs: list[VehicleActionPair],
) -> list[VehicleActionPair]:
    # solve_as_min_cost_flow_problem(vehicle_action_pairs)
    vehicle_action_pairs = or_tools_min_cost_flow(vehicle_action_pairs)
    vehicles = Vehicles.get_vehicles()
    occupied_vehicles = len(list(filter(lambda x: x.is_occupied(), vehicles)))
    relocated_vehicles = len(
        list(
            filter(
                lambda x: x.is_occupied() and x.job.is_relocation,
                vehicles,
            )
        )
    )
    idling_vehicles = len(
        list(filter(lambda x: x.action.is_idling(), vehicle_action_pairs))
    )
    matched_vehicles = len(vehicle_action_pairs) - idling_vehicles
    occupied_vehicles = occupied_vehicles - relocated_vehicles
    LOGGER.debug(
        f"Matched vehicles: {matched_vehicles}, Occupied vehicles: {occupied_vehicles}, Relocated vehicles: {relocated_vehicles}, Idling vehicles: {idling_vehicles}"
    )
    DataCollector.append_workload(State.get_state().current_time, occupied_vehicles)
    for pair in vehicle_action_pairs:
        if pair.action.is_idling():
            continue
        current_time = State.get_state().current_time
        vehicle_zone = Grid.get_instance().find_zone(pair.vehicle.current_position)
        passenger_pu_zone = pair.action.route.order.zone
        passenger_do_zone = Grid.get_instance().find_zone(
            pair.get_vehicle_destination()
        )
        destination_zone = Grid.get_instance().find_zone(pair.action.route.destination)
        vehicle_trip_time = pair.action.route.vehicle_time
        time_reduction = pair.action.route.time_reduction
        combi_route = not pair.action.route.is_regular_route()
        total_vehicle_distance = pair.get_total_vehicle_distance()
        DataCollector.append_trip(
            current_time,
            vehicle_zone,
            passenger_pu_zone,
            passenger_do_zone,
            destination_zone,
            vehicle_trip_time,
            time_reduction,
            combi_route,
            total_vehicle_distance,
        )
    return vehicle_action_pairs
