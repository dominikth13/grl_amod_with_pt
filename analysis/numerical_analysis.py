import csv
import datetime
import os
import re
import numpy as np
import pandas as pd
import shutil
import matplotlib.pyplot as plt
from scipy.spatial.distance import jensenshannon

from analysis.configuration import get_all_multi_comparision_values, get_multi_comparison_values, set_params, get_comparison_values
from params.program_params import Mode, ProgramParams
from program.grid.grid import Grid
from program.location.location import Location


def load_and_merge_data(base_path, filename, dates):
    dfs = []

    for date in dates:
        # Tripdata data
        file_name = f"{filename}{date}.csv"
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            data = pd.read_csv(file_path)
            dfs.append(data)

    if dfs:
        merged_df = pd.concat(dfs, ignore_index=True)
    else:
        merged_df = pd.DataFrame()
    return merged_df


def analyse():
    output_data = {
        "Average time reduction per vehicle per hour in minutes": 0.0,
        "Amount of served orders per day": 0.0,
        "Combi route quota": 0.0,
        "Average vehicle route length in meters": 0.0,
        "Vehicle workload": 0.0,
        "Relocation workload": 0.0,
        "Idling quota": 0.0,
        "Average time reduction per order in minutes": 0.0,
        "Percentage of accepted orders": 0.0,
        "Average distance of relocation in meters": 0.0,
        "Jensen-Shannon-Divergence": 0.0
    }

    base_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data"

    dates = [datetime.date(2023, 7, 24) + datetime.timedelta(days=x) for x in range(7)]

    data = load_and_merge_data(base_path, "tripdata", dates)
    datarl = load_and_merge_data(base_path, "relocation_trip_data", dates)
    datadriver = load_and_merge_data(base_path, "vehicle_data", dates)
    dataorders = load_and_merge_data("data/for_hire", "orders_", dates)

    output_data["Average time reduction per vehicle per hour in minutes"] = round(
        sum(
            data["time_reduction"]
            / 60
            / 24
            / len(dates)
            / ProgramParams.AMOUNT_OF_VEHICLES
        ),
        2,
    )

    output_data["Amount of served orders per day"] = int(len(data) / len(dates))
    output_data["Combi route quota"] = (
        f"{round(100*sum(data['combi_route']/len(data)), 2)}%"
    )
    output_data["Average vehicle route length in meters"] = round(
        sum(data["total_vehicle_distance"] / len(data)), 2
    )

    amount_occupied = datadriver.loc[
        datadriver["status"] == "occupied", "status"
    ].count()
    amount_relocation = datadriver.loc[
        datadriver["status"] == "relocation", "status"
    ].count()
    amount_idling = datadriver.loc[datadriver["status"] == "idling", "status"].count()
    output_data["Vehicle workload"] = (
        f"{round(100*amount_occupied/len(datadriver), 2)}%"
    )
    output_data["Relocation workload"] = (
        f"{round(100*amount_relocation/len(datadriver), 2)}%"
    )
    output_data["Idling quota"] = f"{round(100*amount_idling/len(datadriver), 2)}%"

    total_time_reduction = round(sum(data["time_reduction"] / 60), 2)
    output_data["Average time reduction per order in minutes"] = round(
        total_time_reduction / len(data), 2
    )

    median = data["time_reduction"].median()/60
    upper_qantile = data["time_reduction"].quantile(0.75)/60
    lower_quantile = data["time_reduction"].quantile(0.25)/60
    output_data["Median time reduction per order in minutes"] = round(median, 2)
    output_data["Upper quantile time reduction per order in minutes"] = round(upper_qantile, 2)
    output_data["Lower quantile time reduction per order in minutes"] = round(lower_quantile, 2)

    output_data["Percentage of accepted orders"] = round(
        100 * len(data) / len(dataorders), 2
    )
    output_data["Average distance of relocation in meters"] = round(
        sum(datarl["distance"] / len(datarl)), 2
    )
    output_data["Jensen-Shannon-Divergence"] = round(calculate_vehicle_distribution(datadriver), 4)

    return output_data


def calculate_vehicle_distribution(vehicle_data: pd.DataFrame) -> float:
    subway_distribution = {"Manhattan": 0, "Bronx": 0, "Queens": 0, "Brooklyn": 0}
    with open("data/subway_data_city_parts.csv", mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            subway_distribution[row["city_part"]] += 1

    vehicle_distribution = {"Manhattan": 0, "Bronx": 0, "Queens": 0, "Brooklyn": 0}
    zone_to_city_part = {}
    with open("data/zone_city_parts.csv", mode="r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            zone_to_city_part[int(row["zone_id"])] = row["city_part"]

    grid = Grid.get_instance()
    for _, row in vehicle_data.iterrows():
        vehicle_distribution[
            zone_to_city_part[grid.find_zone(Location(row["lat"], row["lon"])).id]
        ] += 1
    
    subway_list = list(subway_distribution.values())
    vehicle_list = list(vehicle_distribution.values())

    subway_dist = np.array(subway_list) / sum(subway_list)
    vehicle_dist = np.array(vehicle_list) / sum(vehicle_list)

    return jensenshannon(subway_dist, vehicle_dist)

def numerical_analysis():
    set_params()

    result_str = ""

    results = analyse()
    for key in results:
        result_str += f"{key}: {results[key]}\n"

    figure_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    with open(f"{figure_path}/analysis_results.txt", mode="w") as text_file:
        text_file.write(result_str)
    print(result_str)


def numerical_comparison():
    set_params()
    parameter, values = get_comparison_values()
    output_data = {
        "Average time reduction per vehicle per hour in minutes": [],
        "Amount of served orders per day": [],
        "Combi route quota": [],
        "Average vehicle route length in meters": [],
        "Vehicle workload": [],
        "Relocation workload": [],
        "Idling quota": [],
        "Average time reduction per order in minutes": [],
        "Percentage of accepted orders": [],
        "Average distance of relocation in meters": [],
        "Jensen-Shannon-Divergence": []
    }

    for value in values:
        ProgramParams.set_member(parameter, value)

        data = analyse()
        for key in data:
            output_data[key].append(data[key])

    figure_path = f"store/comparisons"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    with open(f"{figure_path}/{parameter}.csv", mode="w") as file:
        writer = csv.writer(file)
        writer.writerow(["Criteria"] + [str(value) for value in values])
        for row in output_data:
            writer.writerow([row] + output_data[row])

def numerical_selected_multi_comparison():
    set_params()
    values = get_multi_comparison_values()
    output_data = {
        "Average time reduction per vehicle per hour in minutes": [],
        "Amount of served orders per day": [],
        "Combi route quota": [],
        "Average vehicle route length in meters": [],
        "Vehicle workload": [],
        "Relocation workload": [],
        "Idling quota": [],
        "Average time reduction per order in minutes": [],
        "Percentage of accepted orders": [],
        "Average distance of relocation in meters": [],
        "Jensen-Shannon-Divergence": []
    }

    for value in values:
        for key in value:
            ProgramParams.set_member(key, value[key])

        data = analyse()
        for key in data:
            output_data[key].append(data[key])

    figure_path = f"store/multi_comparisons"
    file_name = ""
    for value in values:
        for key, value in value.items():
            file_name += f"{key}{value}_"
    file_name.rstrip('_')

    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    with open(f"{figure_path}/{file_name}.csv", mode="w") as file:
        writer = csv.writer(file)
        writer.writerow(["Criteria"] + [paramsettings_to_string(value) for value in values])
        for row in output_data:
            writer.writerow([row] + output_data[row])

def numerical_multi_comparison():
    values = get_all_multi_comparision_values()
    output_data = {
        "Average time reduction per vehicle per hour in minutes": [],
        "Amount of served orders per day": [],
        "Combi route quota": [],
        "Average vehicle route length in meters": [],
        "Vehicle workload": [],
        "Relocation workload": [],
        "Idling quota": [],
        "Average time reduction per order in minutes": [],
        "Percentage of accepted orders": [],
        "Average distance of relocation in meters": [],
        "Jensen-Shannon-Divergence": []
    }

    for value in values:
        set_params()
        for key in value:
            ProgramParams.set_member(key, value[key])

        data = analyse()
        for key in data:
            output_data[key].append(data[key])

    figure_path = f"store/multi_comparisons"
    aov = values[0]["AMOUNT_OF_VEHICLES"]
    file_name = f"comparison_{aov}_vehicles"

    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    with open(f"{figure_path}/{file_name}.csv", mode="w") as file:
        writer = csv.writer(file)
        writer.writerow(["Param Settings"])
        for row in ["AMOUNT_OF_VEHICLES","MAX_IDLING_TIME","DISCOUNT_RATE","LS","LEARNING_RATE","IDLING_COST","RELOCATION_RADIUS","DIRECT_TRIP_DISCOUNT_FACTOR","MAIN_AND_TARGET_NET_SYNC_ITERATIONS"]:
            writer.writerow([row] + ["" if value.get(row) == None else value[row] for value in values])
        writer.writerow(["Criteria"])
        for row in output_data:
            writer.writerow([row] + output_data[row])

def paramsettings_to_string(paramsettings: dict):
    result = ""
    if dict == {}:
        return "Standard"
    
    for key, value in paramsettings.items():
        result += f"{key}{value}_"
    return result.rstrip('_')