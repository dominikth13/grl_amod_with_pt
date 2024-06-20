import csv
from datetime import timedelta
import os
from analysis.numerical_analysis import numerical_analysis, numerical_comparison, numerical_multi_comparison, numerical_selected_multi_comparison
from analysis.plots_comparison import plot_comparison
from params.program_params import Mode, ProgramParams
from params.program_stats import ProgramStats
from program.execution import execute_graph_reinforcement_learning
from program.grid.grid import Grid
from program.order.orders import Orders
from program.state.state import State
from program.state.state_value_networks import StateValueNetworks
from program.vehicle.vehicles import Vehicles
from static_data_generation.public_transport_graph_creation import (
    generate_shortest_paths_graph,
)
from static_data_generation.vehicle_data_initialization import (
    initialize_vehicle_positions,
)
from static_data_generation.zone_graph_creation import create_zone_graph, fix_zone_graph
from visualization.visualize_vehicle_positions import visualize_vehicle_positions
from visualization.visualize_graph import visualize_zone_graph
import analysis.plots as plt

def raze_data():
    StateValueNetworks.raze_weights()
    # Delete files
    if os.path.exists("input_data/average_time_reduction_sat.csv"):
        os.remove("input_data/average_time_reduction_sat.csv")
    if os.path.exists("input_data/average_time_reduction_sun.csv"):
        os.remove("input_data/average_time_reduction_sun.csv")
    if os.path.exists("input_data/average_time_reduction_wd.csv"):
        os.remove("input_data/average_time_reduction_wd.csv")
    if os.path.exists("input_data/vehicles.csv"):
        os.remove("input_data/vehicles.csv")


def grl_train_and_test():
    raze_data()
    initialize_vehicle_positions()
    # Train the algorithm On-Policy
    for i in range(14):
        execute_graph_reinforcement_learning()
        Orders.reset()
        State.reset()
        ProgramStats.SUM_OF_TIMESAFE = 0
        ProgramParams.SIMULATION_DATE += timedelta(1)
    # Testing
    Vehicles.raze_vehicles()
    initialize_vehicle_positions()
    # Test the algorithm On-Policy
    for i in range(7):
        execute_graph_reinforcement_learning()
        Orders.reset()
        State.reset()
        ProgramStats.SUM_OF_TIMESAFE = 0
        ProgramParams.SIMULATION_DATE += timedelta(1)


# Read program params
if os.path.isfile("execution/program_params.csv"):
    with open("execution/program_params.csv", mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            ProgramParams.set_member(row["parameter"], row["value"])
# Read execution file
if os.path.isfile("execution/run.csv"):
    with open("execution/run.csv", mode="r") as file:
        reader = csv.DictReader(file)
        if reader.__next__()["Command"] == "grl":
            ProgramParams.EXECUTION_MODE = Mode.GRAPH_REINFORCEMENT_LEARNING
            if reader.__next__()["Command"] == "train_and_test":
                grl_train_and_test()
                exit()


while True:
    user_input = input(
        "Which menu you want to enter? (Graph Reinforcement Learning -> 1, Static Data Generation -> 2, Visualization -> 3, Data Analysis -> 4) "
    )
    if user_input == "1":
        ProgramParams.EXECUTION_MODE = Mode.GRAPH_REINFORCEMENT_LEARNING
        while True:
            user_input = input(
                "Which script do you want to start? (Online Training and Testing -> 1, Start Graph Reinforcement Learning (one day) -> 2) "
            )
            if user_input == "1":
                grl_train_and_test()
                break
            if user_input == "2":
                initialize_vehicle_positions()
                execute_graph_reinforcement_learning()
                break
            else:
                print("This option is not allowed. Please try again.")
        break

    elif user_input == "2":
        while True:
            user_input = input(
                "Which script do you want to start? (Create Zone Graph -> 1, Create Public Transport Graph -> 2) "
            )
            if user_input == "1":
                create_zone_graph()
                break
            if user_input == "2":
                generate_shortest_paths_graph()
                break
            else:
                print("This option is not allowed. Please try again.")
        break

    elif user_input == "3":
        while True:
            user_input = input(
                "Which script do you want to start? (Visualize Zone Graph -> 1, Visualize vehicle positions -> 2) "
            )
            if user_input == "1":
                visualize_zone_graph()
                break
            elif user_input == "2":
                visualize_vehicle_positions()
                break
            else:
                print("This option is not allowed. Please try again.")
        break

    elif user_input == "4":
        while True:
            print("Please remind to adapt to the correct paths.")
            user_input = input(
                "Which script do you want to start? (Numerical analysis -> 1, Graphical analysis -> 2) "
            )

            if user_input == "1":
                while True:
                    user_input = input(
                        "Which script do you want to start? (Numerical data analysis -> 1, Numerical data comparison -> 2, Numerical selected multi data comparison -> 3, Numerical multi data comparison -> 4) "
                    )
                    if user_input == "1":
                        numerical_analysis()
                        break
                    elif user_input == "2":
                        numerical_comparison()
                        break
                    elif user_input == "3":
                        numerical_selected_multi_comparison()
                        break
                    elif user_input == "4":
                        numerical_multi_comparison()
                        break
                    else:
                        print("This option is not allowed. Please try again.")
                break
            
            elif user_input == "2":
                while True:
                    user_input = input(
                        "Which script do you want to start? (Data analysis -> 1, Data comparison -> 2) "
                    )
                    if user_input == "1":
                        while True:
                            user_input = input(
                                "Which script do you want to start? (\n   Plot average time reduction -> 1\n   Plot average trip distance for direct routes -> 2\n   Plot average trip distance for combination routes -> 3\n   Plot vehicle distribution -> 4\n   Plot combi route ratio -> 5\n   Plot workload -> 6\n) "
                            )
                            if user_input == "1":
                                plt.average_time_reduction_per_day()
                                break
                            elif user_input == "2":
                                plt.average_trip_distances_per_day_for_direct_routes()
                                break
                            elif user_input == "3":
                                plt.average_trip_distances_per_day_for_combination_routes()
                                break
                            elif user_input == "4":
                                plt.visualize_vehicles()
                                break
                            elif user_input == "5":
                                plt.visualize_combi_route_ratio()
                                break
                            elif user_input == "6":
                                plt.visualize_workload()
                                break
                            else:
                                print("This option is not allowed. Please try again.")
                        break
                    elif user_input == "2":
                        plot_comparison()
                        break
                    else:
                        print("This option is not allowed. Please try again.")
                break
                
    
        break

    else:
        print("This option is not allowed. Please try again.")
