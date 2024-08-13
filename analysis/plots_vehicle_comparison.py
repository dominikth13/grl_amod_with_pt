import csv
from datetime import datetime
import os
import re
from statistics import mean
from matplotlib import pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
import geopandas as gpd
from analysis.configuration import get_vehicle_comparison_values, set_params
from analysis.numerical_analysis import calculate_vehicle_distribution
from params.program_params import ProgramParams


def time_reduction_per_order_vehicles():
    vehicle_amounts, vehicle_params = get_vehicle_comparison_values()
    time_reductions = []
    for vehicle_amount in vehicle_amounts:
        set_params()

        for param in vehicle_params[vehicle_amount]:
            ProgramParams.set_member(param, vehicle_params[vehicle_amount][param])

        tripdata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
        time_reduction_per_order = []

        tripdata_files = [
            f
            for f in os.listdir(tripdata_path)
            if f.endswith(".csv") and f.startswith("tripdata")
        ]
        dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in tripdata_files]
        dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))
        dates = dates[-7:]
        for date in dates:
            # Tripdata data
            tripdata_file_name = f"tripdata{date}.csv"
            tripdata_file_path = os.path.join(tripdata_path, tripdata_file_name)
            if os.path.exists(tripdata_file_path):
                tripdata = pd.read_csv(tripdata_file_path)
                time_reduction_per_order.append(
                    tripdata["time_reduction"].sum() / 60 / len(tripdata)
                )
            else:
                time_reduction_per_order.append(float("nan"))

        time_reductions.append(mean(time_reduction_per_order))

    plt.figure(figsize=(12, 6))
    plt.plot(vehicle_amounts, time_reductions, marker="o", linestyle="-", color="orange")
    plt.xlabel("Anzahl der Fahrzeuge")
    plt.ylabel("Zeitersparnis in Minuten")
    plt.ylim(20, 31)
    plt.title("Durchschnittliche Zeitersparnis pro bedienter Order in Minuten")
    plt.grid(True)
    plt.xticks(vehicle_amounts)

    figure_path = f"store/vehicle_comparisons/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/time_reduction_per_order.png")

def served_orders_vehicles():
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    amount_of_orders_per_vehicle(ax[0])
    amount_of_orders(ax[1])
    plt.subplots_adjust(wspace=0.5)
    figure_path = f"store/vehicle_comparisons/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/amount_of_orders.png")
    
def amount_of_orders_per_vehicle(ax):
    vehicle_amounts, vehicle_params = get_vehicle_comparison_values()
    amount_of_orders_per_vehicle = []
    for vehicle_amount in vehicle_amounts:
        set_params()

        for param in vehicle_params[vehicle_amount]:
            ProgramParams.set_member(param, vehicle_params[vehicle_amount][param])

        tripdata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
        amount_of_orders_per_vehicle_per_day = []

        tripdata_files = [
            f
            for f in os.listdir(tripdata_path)
            if f.endswith(".csv") and f.startswith("tripdata")
        ]
        dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in tripdata_files]
        dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))
        dates = dates[-7:]
        for date in dates:
            # Tripdata data
            tripdata_file_name = f"tripdata{date}.csv"
            tripdata_file_path = os.path.join(tripdata_path, tripdata_file_name)
            if os.path.exists(tripdata_file_path):
                tripdata = pd.read_csv(tripdata_file_path)
                amount_of_orders_per_vehicle_per_day.append(
                    len(tripdata) / ProgramParams.AMOUNT_OF_VEHICLES
                )
            else:
                amount_of_orders_per_vehicle_per_day.append(float("nan"))

        amount_of_orders_per_vehicle.append(mean(amount_of_orders_per_vehicle_per_day))

    ax.plot(vehicle_amounts, amount_of_orders_per_vehicle, marker="o", linestyle="-", color="red")
    ax.set_xlabel("Anzahl der Fahrzeuge")
    ax.set_ylabel("Bediente Orders pro Tag pro Fahrzeug")
    ax.set_ylim(60, 74.5)
    ax.set_title("Durchschnittliche Anzahl bedienter Orders pro Tag pro Fahrzeug")
    ax.grid(True)
    ax.set_xticks(vehicle_amounts)

def amount_of_orders(ax):
    vehicle_amounts, vehicle_params = get_vehicle_comparison_values()
    amount_of_orders = []
    for vehicle_amount in vehicle_amounts:
        set_params()

        for param in vehicle_params[vehicle_amount]:
            ProgramParams.set_member(param, vehicle_params[vehicle_amount][param])

        tripdata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
        amount_of_orders_per_day = []

        tripdata_files = [
            f
            for f in os.listdir(tripdata_path)
            if f.endswith(".csv") and f.startswith("tripdata")
        ]
        dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in tripdata_files]
        dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))
        dates = dates[-7:]
        for date in dates:
            # Tripdata data
            tripdata_file_name = f"tripdata{date}.csv"
            tripdata_file_path = os.path.join(tripdata_path, tripdata_file_name)
            if os.path.exists(tripdata_file_path):
                tripdata = pd.read_csv(tripdata_file_path)
                amount_of_orders_per_day.append(len(tripdata))
            else:
                amount_of_orders_per_day.append(float("nan"))

        amount_of_orders.append(mean(amount_of_orders_per_day))

    ax.plot(vehicle_amounts, amount_of_orders, marker="o", linestyle="-", color="darkred")
    ax.set_xlabel("Anzahl der Fahrzeuge")
    ax.set_ylabel("Bediente Orders pro Tag")
    ax.set_ylim(0, 410000)
    ax.set_title("Durchschnittliche Anzahl bedienter Orders pro Tag")
    ax.grid(True)
    ax.set_xticks(vehicle_amounts)

def workload_vehicles():
    vehicle_amounts, vehicle_params = get_vehicle_comparison_values()
    occ = []
    idl = []
    rel = []
    not_idl = []
    for vehicle_amount in vehicle_amounts:
        set_params()

        for param in vehicle_params[vehicle_amount]:
            ProgramParams.set_member(param, vehicle_params[vehicle_amount][param])

        vehicle_data_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
        occupied = []
        idle = []
        relocation = []

        vehicle_data_files = [
            f
            for f in os.listdir(vehicle_data_path)
            if f.endswith(".csv") and f.startswith("vehicle_data")
        ]
        dates = [
            re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in vehicle_data_files
        ]
        dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))
        dates = dates[-7:]
        for date in dates:
            # Tripdata data
            vehicle_data_filename = f"vehicle_data{date}.csv"
            vehicle_data_filepath = os.path.join(vehicle_data_path, vehicle_data_filename)
            if os.path.exists(vehicle_data_filepath):
                vehicle_data = pd.read_csv(vehicle_data_filepath)
                occupied.append(
                    vehicle_data.loc[
                        vehicle_data["status"] == "occupied", "status"
                    ].count()
                    / len(vehicle_data)
                )
                idle.append(
                    vehicle_data.loc[
                        vehicle_data["status"] == "idling", "status"
                    ].count()
                    / len(vehicle_data)
                )
                relocation.append(
                    vehicle_data.loc[
                        vehicle_data["status"] == "relocation", "status"
                    ].count()
                    / len(vehicle_data)
                )

            else:
                occupied.append(float("nan"))
                relocation.append(float("nan"))
                idle.append(float("nan"))

        occ.append(mean(occupied))
        idl.append(mean(idle))
        rel.append(1 - occ[-1] - idl[-1])
        not_idl.append(occ[-1] + rel[-1])
    plt.figure(figsize=(12, 6))
    plt.stackplot(vehicle_amounts, occ, rel, idl, labels=["Besetzt", "Relocation", "Warten"], colors=["#FF6347", "#1f77b4", "#808080"], alpha=0.8)
    plt.plot(vehicle_amounts, np.array(occ), marker="o", color="black")
    plt.plot(vehicle_amounts, np.array(rel) + np.array(occ), marker="o", color="black")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
    plt.xlabel("Anzahl der Fahrzeuge")
    plt.ylabel("Anteile der Fahrzeugnutzung (%)")
    plt.title("Anteile der Fahrzeugnutzung: Besetzt, Relocation, Warten")
    plt.legend(loc="lower right")
    plt.grid(True)
    plt.xticks(vehicle_amounts)

    figure_path = f"store/vehicle_comparisons/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/workload.png")

def combi_route_quota_vehicles():
    vehicle_amounts, vehicle_params = get_vehicle_comparison_values()
    combi_quota = []
    for vehicle_amount in vehicle_amounts:
        set_params()

        for param in vehicle_params[vehicle_amount]:
            ProgramParams.set_member(param, vehicle_params[vehicle_amount][param])

        tripdata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
        combi_quota_per_day = []

        tripdata_files = [
            f
            for f in os.listdir(tripdata_path)
            if f.endswith(".csv") and f.startswith("tripdata")
        ]
        dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in tripdata_files]
        dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))
        dates = dates[-7:]
        for date in dates:
            # Tripdata data
            tripdata_file_name = f"tripdata{date}.csv"
            tripdata_file_path = os.path.join(tripdata_path, tripdata_file_name)
            if os.path.exists(tripdata_file_path):
                tripdata = pd.read_csv(tripdata_file_path)
                combi_quota_per_day.append(len(tripdata[tripdata["combi_route"] == True]) / len(tripdata))
            else:
                combi_quota_per_day.append(float("nan"))

        combi_quota.append(mean(combi_quota_per_day))

    plt.figure(figsize=(12, 6))
    plt.plot(vehicle_amounts, combi_quota, marker="o", linestyle="-", color="green")
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
    plt.xlabel("Anzahl der Fahrzeuge")
    plt.ylabel("Anteil an Kombirouten (%)")
    plt.ylim(0.55, 0.75)
    plt.title("Durchschnittliche Anteil an Kombirouten")
    plt.grid(True)
    plt.xticks(vehicle_amounts)

    figure_path = f"store/vehicle_comparisons/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/combi_route_quota.png")

def vehicle_distribution_vehicles():
    vehicle_amounts, vehicle_params = get_vehicle_comparison_values()
    distribution = []
    for vehicle_amount in vehicle_amounts:
        set_params()

        for param in vehicle_params[vehicle_amount]:
            ProgramParams.set_member(param, vehicle_params[vehicle_amount][param])

        vehicle_data_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
        distribution_per_day = []

        vehicle_data_files = [
            f
            for f in os.listdir(vehicle_data_path)
            if f.endswith(".csv") and f.startswith("vehicle_data")
        ]
        dates = [
            re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in vehicle_data_files
        ]
        dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))
        dates = dates[-7:]
        for date in dates:
            # Tripdata data
            vehicle_data_file_name = f"vehicle_data{date}.csv"
            vehicle_data_file_path = os.path.join(vehicle_data_path, vehicle_data_file_name)
            if os.path.exists(vehicle_data_file_path):
                vehicle_data = pd.read_csv(vehicle_data_file_path)
                distribution_per_day.append(calculate_vehicle_distribution(vehicle_data))
            else:
                distribution_per_day.append(float("nan"))

        distribution.append(mean(distribution_per_day))

    plt.figure(figsize=(12, 6))
    plt.plot(vehicle_amounts, distribution, marker="o", linestyle="-", color="purple")
    plt.xlabel("Anzahl der Fahrzeuge")
    plt.ylabel("Jensen-Shannon Divergenz der räumlichen Verteilung")
    plt.title("Räumliche Verteilung der Fahrzeuge im Vergleich zur Stationsverteilung")
    plt.grid(True)
    plt.xticks(vehicle_amounts)

    figure_path = f"store/vehicle_comparisons/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/vehicle_distribution.png")

def vehicle_postions_vehicles():
    vehicle_amounts, vehicle_params = get_vehicle_comparison_values()
    vehicle_dfs = []
    for vehicle_amount in vehicle_amounts:
        set_params()

        for param in vehicle_params[vehicle_amount]:
            ProgramParams.set_member(param, vehicle_params[vehicle_amount][param])

        vehicledata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"
        
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
        vehicle_dfs.append(pd.DataFrame(vehicledata))

    city_borders = gpd.read_file("data/nyc_city_borders/borders.shp")
    subway_data_path = "data/continuous_subway_data.csv"
    subway_data_df = pd.read_csv(subway_data_path)
    fig, ax = plt.subplots(2, 2, figsize=(12, 12))
    for i in range(2):
        for j in range(2):
            vehicle_amount = vehicle_amounts[i*2+j]
            vehicle_df = vehicle_dfs[i*2+j]
            # Draw city borders
            city_borders.plot(ax=ax[i,j], color="lightgrey", alpha=0.6, label="City borders")

            # Draw stations
            ax[i,j].scatter(subway_data_df["LONG"], subway_data_df["LAT"], c="purple", label="Station", s = 3)

            # Draw vehicles
            ax[i,j].scatter(vehicle_df["lon"], vehicle_df["lat"], c="green", label="Fahrzeug", alpha=0.8**((vehicle_amount if vehicle_amount <= 4000 else 4000) /1000), s = 3)

            ax[i,j].set_xlim(-74.05, -73.69)
            ax[i,j].set_ylim(40.535, 40.92)

            ax[i,j].legend(loc="lower right")

            ax[i,j].set_title(f"{vehicle_amount} Fahrzeuge: Verteilung aller Fahrzeuge\nam Ende des Testzeitraumes in NYC")
            ax[i,j].set_xlabel("Latitude")
            ax[i,j].set_ylabel("Longitude")
    plt.subplots_adjust(hspace=0.3)
    figure_path = f"store/vehicle_comparisons/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/vehicle_location.png", dpi=600)