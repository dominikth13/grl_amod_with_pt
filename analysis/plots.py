import csv
import pandas as pd
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import datetime
import re
from datetime import datetime
from scipy import stats
from shapely.geometry import MultiPoint
from geopandas import GeoSeries, GeoDataFrame
import geopandas as gpd


from analysis.configuration import set_params
from params.program_params import Mode, ProgramParams
from program.location.location import Location

# Some graphics do not work
# The graphics for the paper are from row 1492
def calculate_moving_average(values, window_size):
    """Calculates the moving average with a specific window size."""
    # Extend the values at the beginning to start the moving average from the first point
    extended_values = np.pad(values, (window_size - 1, 0), mode="edge")
    moving_average = np.convolve(
        extended_values, np.ones(window_size) / window_size, mode="valid"
    )
    return moving_average


def calculate_linear_regression(values, window_size):
    """
    Performs a linear regression across the entire dataset.
    The window_size parameter remains unused as linear regression
    is typically applied across the entire dataset.
    """
    # Creating an array with indices as x-values for the linear regression
    x = np.arange(len(values))
    # Performing the linear regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
    # Calculating the y-values of the linear regression
    regression_values = intercept + slope * x
    return regression_values


def average_number_of_drivers_per_day():
    tripdata_path = "store/for_hire/rl_relocation/drivers/1000"
    tripdata_files = [
        f
        for f in os.listdir(tripdata_path)
        if f.endswith(".csv") and f.startswith("tripdata")
    ]

    average_occupied_drivers = []
    # Extract the data from the filenames of the tripdata files and sort them
    dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in tripdata_files]
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))

    for date in dates:
        workload_file_name = f"workload{date}.csv"
        workload_file_path = os.path.join(tripdata_path, workload_file_name)
        if os.path.exists(workload_file_path):
            workload_data = pd.read_csv(workload_file_path)
            average_occupied_drivers.append(
                workload_data["num_of_occupied_driver"].mean()
            )
        else:
            average_occupied_drivers.append(float("nan"))

    # Create a figure with four subplots
    fig, ax1 = plt.subplots(1, 1, figsize=(15, 12))

    # First plot: Number of routes per day
    ax1.bar(dates, average_occupied_drivers, color="blue")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Average occupied drivers")
    ax1.set_title("Average occupied drivers per day")
    ax1.set_xticklabels(dates, rotation=45)
    ax1.set_ylim(0, max(average_occupied_drivers) + 100)
    # Display can be adjusted. Just select what is desired from moving_average.
    # moving average: calculate_moving_average
    # linear regression: calculate_linear_regression
    moving_average = calculate_linear_regression(
        average_occupied_drivers, window_size=3
    )
    ax1.plot(
        dates,
        moving_average,
        color="red",
        marker=".",
        linestyle="-",
        linewidth=2,
        label="Moving average",
    )
    ax1.legend()
    plt.savefig("store/plots/average_number_of_drivers_per_day.png")
    


#average_number_of_drivers_per_day()


def number_of_routes_per_day():

    tripdata_path = "store/for_hire/rl_relocation/drivers/1000"
    tripdata_files = [
        f
        for f in os.listdir(tripdata_path)
        if f.endswith(".csv") and f.startswith("tripdata")
    ]
    routes_per_day = []

    dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in tripdata_files]
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))

    for date in dates:
        # Tripdata data
        tripdata_file_name = f"tripdata{date}.csv"
        tripdata_file_path = os.path.join(tripdata_path, tripdata_file_name)
        if os.path.exists(tripdata_file_path):
            tripdata = pd.read_csv(tripdata_file_path)
            routes_per_day.append(len(tripdata))
        else:
            routes_per_day.append(float("nan"))

    fig, ax2 = plt.subplots(1, 1, figsize=(15, 12))
    # Second plot: Cumulative time savings per day
    ax2.bar(dates, routes_per_day, color="blue")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Number of routes")
    ax2.set_title("Number of routes per day")
    ax2.set_xticklabels(dates, rotation=45)
    # Display can be adjusted. Just select what is desired from moving_average.
    # moving average: calculate_moving_average
    # linear regression: calculate_linear_regression
    moving_average = calculate_linear_regression(routes_per_day, window_size=3)
    ax2.plot(
        dates,
        moving_average,
        color="red",
        marker=".",
        linestyle="-",
        linewidth=2,
        label="Moving average",
    )
    ax2.legend()
    plt.savefig("store/plots/number_of_routes_per_day.png")
    


# number_of_routes_per_day()


def total_time_reduction_per_car_in_minutes():
    tripdata_path = "store/for_hire/rl_relocation/drivers/1000"
    total_time_reduction = []
    total_time_reduction_per_car_in_minutes = []

    tripdata_files = [
        f
        for f in os.listdir(tripdata_path)
        if f.endswith(".csv") and f.startswith("tripdata")
    ]
    dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in tripdata_files]
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))

    for date in dates:
        # Tripdata data
        tripdata_file_name = f"tripdata{date}.csv"
        tripdata_file_path = os.path.join(tripdata_path, tripdata_file_name)
        if os.path.exists(tripdata_file_path):
            tripdata = pd.read_csv(tripdata_file_path)
            total_time_reduction.append(tripdata["time_reduction"].sum())
        else:
            total_time_reduction.append(float("nan"))

    for total_time in total_time_reduction:
        # Divide the total time savings by 100 (for the number of cars) and then by 60 (for minutes)
        if not pd.isna(total_time):
            time_per_car_in_minutes = (total_time / 1000) / 60 / 24
        else:
            time_per_car_in_minutes = float("nan")
        total_time_reduction_per_car_in_minutes.append(time_per_car_in_minutes)

    fig, ax3 = plt.subplots(1, 1, figsize=(15, 12))
    ax3.bar(dates, total_time_reduction_per_car_in_minutes, color="blue")
    ax3.set_xlabel("Date")
    ax3.set_ylabel("Time savings per car (minutes)")
    ax3.set_title("Cumulative time savings per hour per car (minutes)")
    ax3.set_xticklabels(dates, rotation=45)
    # Display can be adjusted. Just select what is desired from moving_average.
    # moving average: calculate_moving_average
    # linear regression: calculate_linear_regression
    moving_average = calculate_linear_regression(
        total_time_reduction_per_car_in_minutes, window_size=3
    )
    ax3.plot(
        dates,
        moving_average,
        color="red",
        marker=".",
        linestyle="-",
        linewidth=2,
        label="Moving average",
    )
    ax3.legend()
    plt.savefig("store/plots/total_time_reduction_per_car_in_minutes.png")
    


# total_time_reduction_per_car_in_minutes()


def average_time_reduction_per_day():
    set_params()

    orders_path = "data/for_hire"
    tripdata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
    total_time_reduction = []
    total_time_reduction_per_car_in_minutes = []

    tripdata_files = [
        f
        for f in os.listdir(tripdata_path)
        if f.endswith(".csv") and f.startswith("tripdata")
    ]
    dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in tripdata_files]
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))

    for date in dates:
        # Tripdata data
        tripdata_file_name = f"tripdata{date}.csv"
        tripdata_file_path = os.path.join(tripdata_path, tripdata_file_name)
        if os.path.exists(tripdata_file_path):
            tripdata = pd.read_csv(tripdata_file_path)
            total_time_reduction.append(tripdata["time_reduction"].sum())
        else:
            total_time_reduction.append(float("nan"))

    for total_time in total_time_reduction:
        # Divide the total time savings by 100 (for the number of cars) and then by 60 (for minutes)
        if not pd.isna(total_time):
            time_per_car_in_minutes = total_time/60/24/ProgramParams.AMOUNT_OF_VEHICLES
        else:
            time_per_car_in_minutes = float("nan")
        total_time_reduction_per_car_in_minutes.append(time_per_car_in_minutes)

    fig, ax4 = plt.subplots(1, 1, figsize=(15, 12))
    # Fourth plot: Insert your code for the fourth plot here
    ax4.bar(dates, total_time_reduction_per_car_in_minutes, color="orange")
    ax4.set_xlabel("Date")
    ax4.set_ylabel("Time reduction in minutes")
    ax4.set_title("Average time reduction per vehicle per hour in minutes")
    ax4.set_xticklabels(dates, rotation=45)
    # Display can be adjusted. Just select what is desired from moving_average.
    # moving average: calculate_moving_average
    # linear regression: calculate_linear_regression
    moving_average = calculate_moving_average(
        total_time_reduction_per_car_in_minutes, window_size=5
    )

    # Adjust 'dates' to ignore the first value
    ax4.plot(
        dates,
        moving_average,
        color="red",
        marker=".",
        linestyle="-",
        linewidth=2,
        label="Moving average",
    )

    plt.legend()

    figure_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/average_time_reduction_per_day.png")


def average_trip_distances_per_day_for_direct_routes():
    set_params()

    tripdata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
    total_time_reduction = []
    routes_per_day = []
    total_time_reduction = []
    average_route_length = {
        "driver_to_pickup_distance_km": [],
        "pickup_to_dropoff_distance_km": [],
    }

    zones = {}
    with open("data/zones.csv", mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            zones[int(row["zone_id"])] = Location(float(row["zone_center_lat"]), float(row["zone_center_lon"]))

    # Define a function to calculate the distance between two zones in kilometers
    def calculate_distance_km(zone1_id, zone2_id):
        if zone1_id in zones and zone2_id in zones:
            return zones[zone1_id].distance_to(zones[zone2_id]) / 1000
        else:
            raise Exception(f"{zone1_id} or {zone2_id} not found")

    tripdata_files = [
        f
        for f in os.listdir(tripdata_path)
        if f.endswith(".csv") and f.startswith("tripdata")
    ]
    dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in tripdata_files]
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))
    for date in dates:
        # Tripdata data
        tripdata_file_name = f"tripdata{date}.csv"
        tripdata_file_path = os.path.join(tripdata_path, tripdata_file_name)
        if os.path.exists(tripdata_file_path):
            tripdata = pd.read_csv(tripdata_file_path)
            routes_per_day.append(len(tripdata))
            total_time_reduction.append(tripdata["time_reduction"].sum())
            # Calculate distances for each trip in the dataset
            tripdata["driver_to_pickup_distance_km"] = tripdata.apply(
                lambda x: calculate_distance_km(
                    x["driver_start_zone_id"], x["passenger_pickup_zone_id"]
                ),
                axis=1,
            )
            tripdata["pickup_to_dropoff_distance_km"] = tripdata.apply(
                lambda x: calculate_distance_km(
                    x["passenger_pickup_zone_id"], x["passenger_dropoff_zone_id"]
                ),
                axis=1,
            )
            tripdata["dropoff_to_destination_distance_km"] = tripdata.apply(
                lambda x: calculate_distance_km(
                    x["passenger_dropoff_zone_id"], x["destination_id"]
                ),
                axis=1,
            )
            average_route_length["driver_to_pickup_distance_km"].append(
                tripdata[tripdata["combi_route"]]["driver_to_pickup_distance_km"].mean()
            )
            average_route_length["pickup_to_dropoff_distance_km"].append(
                tripdata[tripdata["combi_route"]][
                    "pickup_to_dropoff_distance_km"
                ].mean()
            )

        else:
            routes_per_day.append(float("nan"))
            total_time_reduction.append(float("nan"))

        # Orders data

    fig, ax5 = plt.subplots(1, 1, figsize=(15, 12))
    ax5.bar(
        dates,
        average_route_length["driver_to_pickup_distance_km"],
        color="#90EE90",
        label="Vehicle position to pickup point",
    )
    ax5.bar(
        dates,
        average_route_length["pickup_to_dropoff_distance_km"],
        color="green",
        alpha=0.6,
        label="Pickup point to destination",
        bottom=average_route_length["driver_to_pickup_distance_km"],
    )
    ax5.set_xlabel("Date")
    ax5.set_ylabel("Average trip distances per day in km")
    ax5.set_title("Average trip distances per day for direct routes")
    ax5.set_xticklabels(dates, rotation=45)

    plt.legend()

    figure_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/average_trip_distances_per_day_for_direct_routes.png")



def average_trip_distances_per_day_for_combination_routes():
    set_params()

    tripdata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
    total_time_reduction = []
    routes_per_day = []
    routes_per_day = []
    total_time_reduction = []
    average_combi_route_length = {
        "driver_to_pickup_distance_km": [],
        "pickup_to_dropoff_distance_km": [],
        "dropoff_to_destination_distance_km": [],
        "driver_to_dropoff_distance_km": [],
    }

    zones = {}
    with open("data/zones.csv", mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            zones[int(row["zone_id"])] = Location(float(row["zone_center_lat"]), float(row["zone_center_lon"]))

    # Define a function to calculate the distance between two zones in kilometers
    def calculate_distance_km(zone1_id, zone2_id):
        if zone1_id in zones and zone2_id in zones:
            return zones[zone1_id].distance_to(zones[zone2_id]) / 1000
        else:
            raise Exception(f"{zone1_id} or {zone2_id} not found")

    tripdata_files = [
        f
        for f in os.listdir(tripdata_path)
        if f.endswith(".csv") and f.startswith("tripdata")
    ]
    dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in tripdata_files]
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))
    for date in dates:
        # Tripdata data
        tripdata_file_name = f"tripdata{date}.csv"
        tripdata_file_path = os.path.join(tripdata_path, tripdata_file_name)
        if os.path.exists(tripdata_file_path):
            tripdata = pd.read_csv(tripdata_file_path)
            routes_per_day.append(len(tripdata))
            total_time_reduction.append(tripdata["time_reduction"].sum())
            # Calculate distances for each trip in the dataset
            tripdata["driver_to_pickup_distance_km"] = tripdata.apply(
                lambda x: calculate_distance_km(
                    x["driver_start_zone_id"], x["passenger_pickup_zone_id"]
                ),
                axis=1,
            )
            tripdata["pickup_to_dropoff_distance_km"] = tripdata.apply(
                lambda x: calculate_distance_km(
                    x["passenger_pickup_zone_id"], x["passenger_dropoff_zone_id"]
                ),
                axis=1,
            )
            tripdata["dropoff_to_destination_distance_km"] = tripdata.apply(
                lambda x: calculate_distance_km(
                    x["passenger_dropoff_zone_id"], x["destination_id"]
                ),
                axis=1,
            )

            average_combi_route_length["driver_to_pickup_distance_km"].append(
                tripdata[tripdata["combi_route"]]["driver_to_pickup_distance_km"].mean()
            )

            average_combi_route_length["pickup_to_dropoff_distance_km"].append(
                tripdata[tripdata["combi_route"]][
                    "pickup_to_dropoff_distance_km"
                ].mean()
            )

            average_combi_route_length["driver_to_dropoff_distance_km"].append(
                average_combi_route_length["driver_to_pickup_distance_km"][-1]
                + average_combi_route_length["pickup_to_dropoff_distance_km"][-1]
            )

            average_combi_route_length["dropoff_to_destination_distance_km"].append(
                tripdata[tripdata["combi_route"]][
                    "dropoff_to_destination_distance_km"
                ].mean()
            )

        else:
            routes_per_day.append(float("nan"))
            total_time_reduction.append(float("nan"))

    fig, ax6 = plt.subplots(1, 1, figsize=(15, 12))
    # Combined plot
    ax6.bar(
        dates,
        average_combi_route_length["driver_to_pickup_distance_km"],
        color="#90EE90",
        label="Vehicle position to pickup point",
    )
    ax6.bar(
        dates,
        average_combi_route_length["pickup_to_dropoff_distance_km"],
        color="green",
        label="Pickup point to station",
        bottom=average_combi_route_length["driver_to_pickup_distance_km"],
    )
    ax6.bar(
        dates,
        average_combi_route_length["dropoff_to_destination_distance_km"],
        color="#006400",
        label="Station to destination",
        bottom=average_combi_route_length["driver_to_dropoff_distance_km"],
    )
    ax6.set_xlabel("Date")
    ax6.set_ylabel("Average trip distances per day in km")
    ax6.set_title("Average trip distances per day for combination routes")
    ax6.set_xticklabels(dates, rotation=45)

    plt.legend()

    figure_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/average_trip_distances_per_day_for_combination_routes.png")


def visualize_combi_route_ratio():
    set_params()

    tripdata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
    routes_per_day = []
    direct_routes_per_day = []
    combi_routes_per_day = []

    tripdata_files = [
        f
        for f in os.listdir(tripdata_path)
        if f.endswith(".csv") and f.startswith("tripdata")
    ]
    dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in tripdata_files]
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))
    for date in dates:
        # Tripdata data
        tripdata_file_name = f"tripdata{date}.csv"
        tripdata_file_path = os.path.join(tripdata_path, tripdata_file_name)
        if os.path.exists(tripdata_file_path):
            tripdata = pd.read_csv(tripdata_file_path)
            routes_per_day.append(len(tripdata))
            direct_routes_per_day.append(len(tripdata[tripdata["combi_route"] == False]))
            combi_routes_per_day.append(len(tripdata[tripdata["combi_route"] == True]))
        else:
            routes_per_day.append(float("nan"))
            direct_routes_per_day.append(float("nan"))
            combi_routes_per_day.append(float("nan"))
    
    fig, ax5 = plt.subplots(1, 1, figsize=(15, 12))
    
    # Direktrouten Balken
    ax5.bar(
        dates,
        direct_routes_per_day,
        color="#90EE90",
        label="Direktrouten",
    )

    # Gleitender Durchschnitt - Direktrouten
    moving_average_direct = calculate_moving_average(
        direct_routes_per_day, window_size=5
    )

    ax5.plot(
        dates,
        moving_average_direct,
        color="red",
        marker=".",
        linestyle="-",
        linewidth=2,
        label="Gleitender Durchschnitt - Direktrouten",
    )

    # Kombirouten Balken
    ax5.bar(
        dates,
        combi_routes_per_day,
        color="green",
        alpha=0.6,
        label="Kombirouten",
        bottom=direct_routes_per_day,
    )

    # Gleitender Durchschnitt - Bediente Orders
    total_routes_per_day = [a + b for a, b in zip(direct_routes_per_day, combi_routes_per_day)]
    moving_average_total = calculate_moving_average(
        total_routes_per_day, window_size=5
    )

    ax5.plot(
        dates,
        moving_average_total,
        color="blue",
        marker=".",
        linestyle="-",
        linewidth=2,
        label="Gleitender Durchschnitt - Bediente Orders",
    )

    # Trennlinie zwischen Trainings- und Testzeitraum
    # Den numerischen Index für die x-Position der Trennlinie verwenden
    split_date_index = dates.index('2023-07-23')
    # Positioniere die Linie zwischen den Indizes 23. und 24. Juli
    line_position = split_date_index + 0.5

    ax2 = ax5.twinx()  # zweite Achse auf der gleichen Figur
    ax2.axvline(x=line_position, color='black', linestyle='--', linewidth=2, zorder=10)
    ax2.set_yticks([])  # Verstecke die Y-Achse der zweiten Achse, da sie nicht benötigt wird

    # Training und Test-Beschriftung
    ax5.text(line_position - 3, max(total_routes_per_day) * 1.02, "Trainingsphase", horizontalalignment='center', color='black', fontsize=14, weight='bold')
    ax5.text(line_position + 2, max(total_routes_per_day) * 1.02, "Testphase", horizontalalignment='center', color='black', fontsize=14, weight='bold')



    # Achsenbeschriftungen und Titel mit größerer Schriftgröße
    ax5.set_xlabel("Datum", fontsize=14)
    ax5.set_ylabel("Anzahl bedienter Orders", fontsize=14)
    ax5.set_title("Verhältnis zwischen Direkt- und Kombirouten pro Tag bei 4000 Fahrzeugen", fontsize=18)
    ax5.set_xticklabels(dates, rotation=45)

    # Legende
    ax5.legend(fontsize=12)

    # Speichern der Figur
    figure_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/combi_route_ratio.png")



def visualize_vehicles():
    set_params()

    grid_cells_path = 'data/grid_cells.csv'
    subway_data_path = 'data/continuous_subway_data.csv'
    vehicledata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
    grid_cells_df = pd.read_csv(grid_cells_path)
    subway_data_df = pd.read_csv(subway_data_path)
    
    vehicledata_files = [
        f
        for f in os.listdir(vehicledata_path)
        if f.endswith(".csv") and f.startswith("vehicle_data")
    ]
    dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in vehicledata_files]
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=True)
    vehicledata_file_name = f"vehicle_data{dates[0]}.csv"
    vehicledata_file_path = os.path.join(vehicledata_path, vehicledata_file_name)
    if os.path.exists(vehicledata_file_path):
        vehicledata = []
        with open(vehicledata_file_path, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if int(row["total_seconds"]) == 82800:
                    vehicledata.append({"lat": float(row["lat"]), "lon": float(row["lon"])})
    vehicle_data_df = pd.DataFrame(vehicledata)

    city_borders = gpd.read_file("data/nyc_city_borders/borders.shp")

    fig, ax = plt.subplots(figsize=(12, 12))

    # Draw city borders
    city_borders.plot(ax=ax, color='lightgrey', alpha=0.6, label='City borders')

    # Draw stations
    plt.scatter(subway_data_df['LONG'], subway_data_df['LAT'], c='purple', label='Stations', alpha=0.7, s = 3)

    # Draw vehicles
    plt.scatter(vehicle_data_df['lon'], vehicle_data_df['lat'], c='green', label='Vehicles', alpha=0.7, s = 20)

    plt.xlim(-74.05, -73.69)  # longitude
    plt.ylim(40.535, 40.92)    # latitude

    plt.legend()

    plt.title("Distribution of Vehicles at the end of observed period")
    plt.xlabel("Latitude")
    plt.ylabel("Longitude")

    figure_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/vehicle_distribution.png", dpi=600)


def visualize_workload():
    set_params()

    workloaddata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
    workload_per_day = []

    workloaddata_files = [
        f
        for f in os.listdir(workloaddata_path)
        if f.endswith(".csv") and f.startswith("workload")
    ]
    dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in workloaddata_files]
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))
    for date in dates:
        # Tripdata data
        workloaddata_file_name = f"workload{date}.csv"
        workloaddata_file_path = os.path.join(workloaddata_path, workloaddata_file_name)
        if os.path.exists(workloaddata_file_path):
            workloaddata = pd.read_csv(workloaddata_file_path)
            workload_per_day.append(
                workloaddata["num_of_occupied_driver"].mean() / ProgramParams.AMOUNT_OF_VEHICLES
            )

        else:
            workload_per_day.append(float("nan"))
    
    fig, ax5 = plt.subplots(1, 1, figsize=(15, 12))
    ax5.bar(
        dates,
        workload_per_day,
        color="#90EE90",
        label="Workload",
    )
    ax5.set_xlabel("Date")
    ax5.set_ylabel("Workload percentage")
    ax5.set_title("Workload of vehicles")
    ax5.set_xticklabels(dates, rotation=45)

    moving_average = calculate_moving_average(
        workload_per_day, window_size=5
    )

    # Adjust 'dates' to ignore the first value
    ax5.plot(
        dates,
        moving_average,
        color="red",
        marker=".",
        linestyle="-",
        linewidth=2,
        label="Moving average",
    )

    plt.ylim(0.7, 1)


    figure_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/workload.png")