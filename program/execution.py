from multiprocessing import Pool
import time

from params.concurrency_params import ConcurrencyParams
from params.program_params import ProgramParams, ProgramStage
from params.program_stats import ProgramStats
from program.algorithm.algorithm import (
    generate_routes,
    generate_vehicle_action_pairs,
    solve_optimization_problem,
)
from program.concurrency.helper_functions import dispatch_order
from program.data_collector import DataCollector
from program.grid.grid import Grid
from program.interval.time import Time
from program.interval.time_series import TimeSeries
from program.logger import LOGGER
from program.order.order import Order
from program.order.orders import Orders
from program.public_transport.fastest_station_connection_network import (
    FastestStationConnectionNetwork,
)
from program.state.state import State
from program.state.state_value_networks import StateValueNetworks
from program.vehicle.vehicles import Vehicles
from program.zone.zone_graph import ZoneGraph


def execute_graph_reinforcement_learning():
    # 1. Initialize environment data
    start_time = time.time()
    LOGGER.info("Initialize Grid")
    Grid.get_instance()
    LOGGER.info("Initialize zone graph")
    ZoneGraph.get_instance()
    LOGGER.info("Initialize time series")
    TimeSeries.get_instance()
    LOGGER.info("Initialize state value networks")
    StateValueNetworks.get_instance()
    LOGGER.info("Initialize state")
    State.get_state()
    LOGGER.info("Initialize fastest connection network")
    FastestStationConnectionNetwork.get_instance()
    LOGGER.info("Initialize orders")
    Orders.get_orders_by_time()
    LOGGER.info("Initialize vehicles")
    Vehicles.get_vehicles()

    StateValueNetworks.get_instance().import_weights()

    # 2. Run Graph Reinforcement Learning algorithm
    for current_total_minutes in range(
        TimeSeries.get_instance().start_time.to_total_minutes(),
        TimeSeries.get_instance().end_time.to_total_minutes() + 1,
    ):
        current_time = Time.of_total_minutes(current_total_minutes)
        LOGGER.info(f"Simulate time {current_time}")

        # Dispatch Orders
        before_timestamp = time.time()
        dispatch_orders(Orders.get_orders_by_time()[current_time])

        # Save runtime
        after_timestamp = time.time()
        ProgramStats.RUNTIME[ProgramStage.ORDER_DISPATCHING] += (after_timestamp - before_timestamp)
        before_timestamp = after_timestamp

        # Update state
        State.get_state().update_state()

        # Initialize state value networks
        StateValueNetworks.get_instance().initialize_iteration()

        # Save runtime
        after_timestamp = time.time()
        ProgramStats.RUNTIME[ProgramStage.VALUE_FUNC_UPDATE] += (after_timestamp - before_timestamp)
        before_timestamp = after_timestamp

        # Generate routes
        LOGGER.debug("Generate routes")
        order_routes_dict = generate_routes(
            list(State.get_state().orders_dict.values())
        )

        # Save runtime
        after_timestamp = time.time()
        ProgramStats.RUNTIME[ProgramStage.ROUTE_GENERATION] += (after_timestamp - before_timestamp)
        before_timestamp = after_timestamp

        # Generate Vehicle-Action pairs with all available routes and vehicles
        LOGGER.debug("Generate vehicle-action-pairs")
        vehicle_action_pairs = generate_vehicle_action_pairs(order_routes_dict)

        # Save runtime
        after_timestamp = time.time()
        ProgramStats.RUNTIME[ProgramStage.VEHICLE_ACTION_PAIRING] += (after_timestamp - before_timestamp)
        before_timestamp = after_timestamp

        # Find vehicle-action matches based on a min-cost-flow problem
        LOGGER.debug("Generate vehicle-action matches")
        matches = solve_optimization_problem(vehicle_action_pairs)

        # Save runtime
        after_timestamp = time.time()
        ProgramStats.RUNTIME[ProgramStage.VOM] += (after_timestamp - before_timestamp)
        before_timestamp = after_timestamp

        # Apply state changes based on Action-Driver matches and existing driver jobs
        LOGGER.debug("Apply simulation changes")
        State.get_state().apply_state_change(matches)

        # Save runtime
        after_timestamp = time.time()
        ProgramStats.RUNTIME[ProgramStage.SIM_UPDATE] += (after_timestamp - before_timestamp)
        before_timestamp = after_timestamp

        # Apply state value changes
        LOGGER.debug("Apply state-value function changes")
        State.get_state().update_state_value_function()

        # Save runtime
        after_timestamp = time.time()
        ProgramStats.RUNTIME[ProgramStage.VALUE_FUNC_UPDATE] += (after_timestamp - before_timestamp)
        before_timestamp = after_timestamp

        if (
            ProgramParams.FEATURE_RELOCATION_ENABLED()
            and current_time.to_total_seconds() % ProgramParams.MAX_IDLING_TIME == 0
        ):
            LOGGER.debug("Relocate long time idle vehicles")
            State.get_state().relocate()
        if current_time.to_total_minutes() % 60 == 0:
            for vehicle in Vehicles.get_vehicles():
                status = (
                    "idling"
                    if not vehicle.is_occupied()
                    else ("relocation" if vehicle.job.is_relocation else "occupied")
                )
                DataCollector.append_driver_data(
                    current_time, vehicle.id, status, vehicle.current_position
                )
                DataCollector.append_zone_id(
                    current_time,
                    Grid.get_instance().find_cell(vehicle.current_position).id,
                )
        
        # Save runtime
        after_timestamp = time.time()
        ProgramStats.RUNTIME[ProgramStage.RE] += (after_timestamp - before_timestamp)
        before_timestamp = after_timestamp

        # Update the expiry durations of still open orders
        State.get_state().update_order_expiry_duration()

        # Increment to next interval
        State.get_state().increment_time_interval(current_time)

        # Save runtime
        after_timestamp = time.time()
        ProgramStats.RUNTIME[ProgramStage.SIM_UPDATE] += (after_timestamp - before_timestamp)
        before_timestamp = after_timestamp

    LOGGER.info("Exporting final vehicle positions")
    Vehicles.export_vehicles()
    LOGGER.info("Exporting average time reductions")
    State.get_state().export_average_time_reductions()
    LOGGER.info("Exporting data")
    DataCollector.export_all_data()
    LOGGER.info("Exporting training results")
    StateValueNetworks.get_instance().export_weights()
    LOGGER.info("Exporting runtime values")
    ProgramStats.export_to_csv()
    LOGGER.info(f"Algorithm took {time.time() - start_time} seconds to run.")

    DataCollector.clear()


def dispatch_orders(orders: list[Order]):
    start = time.time()
    LOGGER.debug(f"Dispatch orders")
    if ConcurrencyParams.FEATURE_ORDER_DISPATCHING_CONCURRENT:
        with Pool(
            processes=ConcurrencyParams.AMOUNT_OF_PROCESSES
        ) as pool:  # adjust the amount of processes to available cores
            orders = pool.map(dispatch_order, orders)
    else:
        for order in orders:
            order.dispatch()
    # Add orders to state
    State.get_state().add_orders(orders)
    end = time.time()
    LOGGER.debug(f"The order dispatching took {round((end - start)*1000,4)} ms.")
