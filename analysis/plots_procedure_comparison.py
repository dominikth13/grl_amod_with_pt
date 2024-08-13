import csv
from datetime import datetime
import os
import re
import geopandas as gpd
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from analysis.configuration import get_procedure_comparison_values, set_params
from params.program_params import ProgramParams
import seaborn as sns


def vehicle_postions_procedures():
    procedures, vehicle_params = get_procedure_comparison_values()
    vehicle_dfs = []
    proc_vehicle_pairs = []
    for procedure in procedures:
        for vehicle_amount in vehicle_params[procedure]:
            proc_vehicle_pairs.append((procedure, vehicle_amount))
            set_params()

            for param in vehicle_params[procedure][vehicle_amount]:
                ProgramParams.set_member(param, vehicle_params[procedure][vehicle_amount][param])

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
    fig, ax = plt.subplots(3, 2, figsize=(12, 16))
    vehicle_amounts = list(vehicle_params[procedures[0]])
    for i in range(2):
        for j in range(3):
            axs = ax[j,i]
            procedure, vehicle_amount = proc_vehicle_pairs[i*3+j]
            vehicle_df = vehicle_dfs[i*3+j]
            # Draw city borders
            city_borders.plot(ax=axs, color="lightgrey", alpha=0.6, label="City borders")

            # Draw stations
            axs.scatter(subway_data_df["LONG"], subway_data_df["LAT"], c="purple", label="Station", s = 2)

            # Draw vehicles
            axs.scatter(vehicle_df["lon"], vehicle_df["lat"], c="green", label="Fahrzeug", alpha=0.8**((vehicle_amount if vehicle_amount <= 4000 else 4000) /1000), s = 3)
            sns.kdeplot(
                x=vehicle_df["lon"], y=vehicle_df["lat"], ax=axs, fill=True, cmap="inferno", alpha=0.8
            )
            axs.set_xlim(-74.05, -73.69)
            axs.set_ylim(40.535, 40.92)

            axs.legend(loc="lower right")
            procedure = "GRL" if procedure == "grl" else "QL"
            axs.set_title(f"{procedure}, {vehicle_amount} Fahrzeuge: Verteilung aller Fahrzeuge\nam Ende des Testzeitraumes in NYC")
            axs.set_xlabel("Latitude")
            axs.set_ylabel("Longitude")
    plt.subplots_adjust(hspace=0.3)
    figure_path = f"store/procedure_comparisons/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/vehicle_location_proc_comp.png", dpi=600)

def usage_and_rejection_procedures():
    procedures, vehicle_params = get_procedure_comparison_values()
    proc_vehicle_pairs = []
    activities = []
    for procedure in procedures:
        for vehicle_amount in vehicle_params[procedure]:
            proc_vehicle_pairs.append((procedure, vehicle_amount))
            set_params()

            for param in vehicle_params[procedure][vehicle_amount]:
                ProgramParams.set_member(param, vehicle_params[procedure][vehicle_amount][param])

            # Dateien laden
            vehicle_data_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data/vehicle_data2023-07-24.csv"
            order_data_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}/data/order_data2023-07-24.csv"
            dispatch_data_path = "data/for_hire/orders_2023-07-24.csv"

            vehicle_data = pd.read_csv(vehicle_data_path)
            order_data = pd.read_csv(order_data_path)
            dispatch_data = pd.read_csv(dispatch_data_path)

            # Konvertierung der pickup_time-Spalte in datetime-Format
            dispatch_data['pickup_time'] = pd.to_datetime(dispatch_data['pickup_time'], format='%H:%M:%S')

            # Extrahieren der Stunde aus der pickup_time-Spalte
            dispatch_data['hour'] = dispatch_data['pickup_time'].dt.hour

            # Aggregation der Daten nach Stunde
            dispatch_activity_per_hour = dispatch_data.groupby('hour').size().reset_index(name='counts')

            # Extrahieren der Stunde aus den Zeitstempeln
            vehicle_data['hour'] = (vehicle_data['total_seconds'] // 3600).astype(int)
            order_data['hour'] = (order_data['total_seconds'] // 3600).astype(int)

            # Berechnen der Anzahl der abgelehnten Bestellungen
            order_data['rejected_requests'] = order_data['quota_of_unserved_orders'] * (order_data['num_of_served_orders'] / (1 - order_data['quota_of_unserved_orders']))
            # Berechnen der gesamten Bestellungen
            order_data['total_requests'] = order_data['num_of_served_orders'] + order_data['rejected_requests']

            # Aggregieren der Daten nach Stunde und Status für Fahrzeugaktivität
            vehicle_activity_per_hour = vehicle_data.groupby(['hour', 'status']).size().unstack(fill_value=0)
            # Berechnen des prozentualen Anteils der Fahrzeugaktivität pro Stunde
            vehicle_activity_per_hour = vehicle_activity_per_hour.div(vehicle_activity_per_hour.sum(axis=1), axis=0).multiply(100)

            # Aggregieren der Daten nach Stunde für Bestellungen (bediente und abgelehnte Bestellungen summieren)
            order_activity_per_hour = order_data.groupby('hour').agg({'num_of_served_orders': 'sum'})

            # Erstellen des DataFrames für die Grafik
            activity_per_hour = vehicle_activity_per_hour.copy()
            activity_per_hour['total_requests'] = dispatch_activity_per_hour['counts']
            activity_per_hour['num_of_served_orders'] = order_activity_per_hour['num_of_served_orders']
            activity_per_hour = activity_per_hour.fillna(0)

            # Sicherstellen, dass alle Stunden von 0 bis 23 enthalten sind
            hours = np.arange(24)
            activity_per_hour = activity_per_hour.reindex(hours, fill_value=0)

            # Sicherstellen, dass alle benötigten Spalten vorhanden sind
            required_columns = ['occupied', 'idling', 'relocation', 'total_requests', 'num_of_served_orders']
            for column in required_columns:
                if column not in activity_per_hour.columns:
                    activity_per_hour[column] = 0
            
            activities.append(activity_per_hour)

    fig, ax = plt.subplots(3, 2, figsize=(12, 16))
    ax1 = None
    ax2 = None
    for i in range(2):
        for j in range(3):
            axs = ax[j,i]
            procedure, vehicle_amount = proc_vehicle_pairs[i*3+j]
            activity_per_hour = activities[i*3+j]

            # Fahrzeugaktivität darstellen
            axs.stackplot(activity_per_hour.index,
                        activity_per_hour['occupied'], 
                        activity_per_hour['relocation'],
                        activity_per_hour['idling'], 
                        labels=['Besetzt', 'Relocation', 'Warten'], 
                        colors=["#FF6347", "#1f77b4", "#808080"])

            axs.set_xlabel('Tageszeit')
            axs.set_ylabel('Anteil der Fahrzeuge [%]')
            axs.set_ylim([0, 100])

            # Zweite y-Achse für Bestellanfragen
            axs2 = axs.twinx()
            axs2.plot(activity_per_hour.index, activity_per_hour['total_requests'], 'k-', label='Anzahl aller Orders')
            axs2.plot(activity_per_hour.index, activity_per_hour['num_of_served_orders'], 'b-', label='Anzahl bedienter Orders')
            axs2.set_ylabel('Anzahl der Orders')
            axs2.set_ylim([0, 35000])

            procedure = "GRL" if procedure == "grl" else "QL"
            axs.set_title(f"{procedure}, {vehicle_amount} Fahrzeuge")
            if ax1 is None:
                ax1 = axs 
                ax2 = axs2

        # Legenden unterhalb des Plots hinzufügen
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    plt.legend(handles1 + handles2, labels1 + labels2, bbox_to_anchor=(0.5, 0), loc="lower center",
                bbox_transform=fig.transFigure, ncol=3, prop={'size': 16})
    plt.subplots_adjust(bottom=0.1, wspace=0.4, hspace=0.5)  # Platz für die Legende unterhalb des Plots
    figure_path = f"store/procedure_comparisons/figures"
    if not os.path.exists(figure_path):
        os.makedirs(figure_path)
    plt.savefig(f"{figure_path}/usage_and_rejection_procedures.png", dpi=600)

# def usage_and_rejection_procedures():
#     procedures, vehicle_params = get_procedure_comparison_values()
#     proc_vehicle_pairs = []
#     activities = []
#     for procedure in ["rl"]:
#         for vehicle_amount in [2000, "2000"]:
#             proc_vehicle_pairs.append((procedure, vehicle_amount))
#             set_params()

#             ProgramParams.set_member("EXECUTION_MODE", "rl")

#             no_re = "/no_re" if vehicle_amount == "2000" else ""
#             # Dateien laden
#             vehicle_data_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}{no_re}/data/vehicle_data2023-07-24.csv"
#             order_data_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}{no_re}/data/order_data2023-07-24.csv"
#             dispatch_data_path = "data/for_hire/orders_2023-07-24.csv"

#             vehicle_data = pd.read_csv(vehicle_data_path)
#             order_data = pd.read_csv(order_data_path)
#             dispatch_data = pd.read_csv(dispatch_data_path)

#             # Konvertierung der pickup_time-Spalte in datetime-Format
#             dispatch_data['pickup_time'] = pd.to_datetime(dispatch_data['pickup_time'], format='%H:%M:%S')

#             # Extrahieren der Stunde aus der pickup_time-Spalte
#             dispatch_data['hour'] = dispatch_data['pickup_time'].dt.hour

#             # Aggregation der Daten nach Stunde
#             dispatch_activity_per_hour = dispatch_data.groupby('hour').size().reset_index(name='counts')

#             # Extrahieren der Stunde aus den Zeitstempeln
#             vehicle_data['hour'] = (vehicle_data['total_seconds'] // 3600).astype(int)
#             order_data['hour'] = (order_data['total_seconds'] // 3600).astype(int)

#             # Berechnen der Anzahl der abgelehnten Bestellungen
#             order_data['rejected_requests'] = order_data['quota_of_unserved_orders'] * (order_data['num_of_served_orders'] / (1 - order_data['quota_of_unserved_orders']))
#             # Berechnen der gesamten Bestellungen
#             order_data['total_requests'] = order_data['num_of_served_orders'] + order_data['rejected_requests']

#             # Aggregieren der Daten nach Stunde und Status für Fahrzeugaktivität
#             vehicle_activity_per_hour = vehicle_data.groupby(['hour', 'status']).size().unstack(fill_value=0)
#             # Berechnen des prozentualen Anteils der Fahrzeugaktivität pro Stunde
#             vehicle_activity_per_hour = vehicle_activity_per_hour.div(vehicle_activity_per_hour.sum(axis=1), axis=0).multiply(100)

#             # Aggregieren der Daten nach Stunde für Bestellungen (bediente und abgelehnte Bestellungen summieren)
#             order_activity_per_hour = order_data.groupby('hour').agg({'num_of_served_orders': 'sum'})

#             # Erstellen des DataFrames für die Grafik
#             activity_per_hour = vehicle_activity_per_hour.copy()
#             activity_per_hour['total_requests'] = dispatch_activity_per_hour['counts']
#             activity_per_hour['num_of_served_orders'] = order_activity_per_hour['num_of_served_orders']
#             activity_per_hour = activity_per_hour.fillna(0)
#             # Sicherstellen, dass alle Stunden von 0 bis 23 enthalten sind
#             hours = np.arange(24)
#             activity_per_hour = activity_per_hour.reindex(hours, fill_value=0)

#             # Sicherstellen, dass alle benötigten Spalten vorhanden sind
#             required_columns = ['occupied', 'idling', 'relocation', 'total_requests', 'num_of_served_orders']
#             for column in required_columns:
#                 if column not in activity_per_hour.columns:
#                     activity_per_hour[column] = 0
            
#             activities.append(activity_per_hour)

#     fig, ax = plt.subplots(1, 2, figsize=(20, 9))
#     ax1 = None
#     ax2 = None
#     for i in range(2):
#         for j in range(1):
#             axs = ax[i]
#             procedure, vehicle_amount = proc_vehicle_pairs[i+j]
#             activity_per_hour = activities[i+j]

#             # Fahrzeugaktivität darstellen
#             axs.stackplot(activity_per_hour.index,
#                         activity_per_hour['occupied'], 
#                         activity_per_hour['relocation'],
#                         activity_per_hour['idling'], 
#                         labels=['occupied', 'relocating', 'idle'], 
#                         colors=["#FF6347", "#1f77b4", "#808080"])

#             axs.set_xlabel('time of day')
#             axs.set_ylabel('fraction of vehicles [%]')
#             axs.set_ylim([0, 100])

#             # Zweite y-Achse für Bestellanfragen
#             axs2 = axs.twinx()
#             axs2.plot(activity_per_hour.index, activity_per_hour['total_requests'], 'k-', label='total orders')
#             axs2.plot(activity_per_hour.index, activity_per_hour['num_of_served_orders'], 'b-', label='served orders')
#             axs2.set_ylabel('number of orders')
#             axs2.set_ylim([0, 35000])

#             procedure = "QLRE" if vehicle_amount == 2000 else "QL"
#             axs.set_title(f"{procedure}, 2000 vehicles")
#             if ax1 is None:
#                 ax1 = axs 
#                 ax2 = axs2

#         # Legenden unterhalb des Plots hinzufügen
#     handles1, labels1 = ax1.get_legend_handles_labels()
#     handles2, labels2 = ax2.get_legend_handles_labels()

#     plt.legend(handles1 + handles2, labels1 + labels2, bbox_to_anchor=(0.5, 0), loc="lower center",
#                 bbox_transform=fig.transFigure, ncol=3, prop={'size': 12})
#     plt.subplots_adjust(wspace=0.3, hspace=0.3)
#     plt.subplots_adjust(bottom=0.2)  # Platz für die Legende unterhalb des Plots
#     figure_path = f"store/procedure_comparisons/figures"
#     if not os.path.exists(figure_path):
#         os.makedirs(figure_path)
#     plt.savefig(f"{figure_path}/usage_and_rejection_procedures.png", dpi=600)

# def vehicle_postions_procedures():
#     procedures, vehicle_params = get_procedure_comparison_values()
#     vehicle_dfs = []
#     proc_vehicle_pairs = []
#     for procedure in ["rl"]:
#         for vehicle_amount in [2000, "2000"]:
#             proc_vehicle_pairs.append((procedure, vehicle_amount))
#             set_params()

#             ProgramParams.set_member("EXECUTION_MODE", "rl")

#             no_re = "/no_re" if vehicle_amount == "2000" else ""
#             vehicledata_path = f"store/{ProgramParams.DATA_OUTPUT_FILE_PATH()}{no_re}/data"
            
#             vehicledata_files = [
#                 f
#                 for f in os.listdir(vehicledata_path)
#                 if f.endswith(".csv") and f.startswith("vehicle_data")
#             ]
#             dates = [re.search(r"(\d{4}-\d{2}-\d{2})", f).group(1) for f in vehicledata_files]
#             dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"), reverse=True)
#             vehicledata_file_name = f"vehicle_data{dates[0]}.csv"
#             vehicledata_file_path = os.path.join(vehicledata_path, vehicledata_file_name)
#             if os.path.exists(vehicledata_file_path):
#                 vehicledata = []
#                 with open(vehicledata_file_path, mode="r") as file:
#                     reader = csv.DictReader(file)
#                     for row in reader:
#                         if int(row["total_seconds"]) == 82800:
#                             vehicledata.append({"lat": float(row["lat"]), "lon": float(row["lon"])})
#             vehicle_dfs.append(pd.DataFrame(vehicledata))

#     city_borders = gpd.read_file("data/nyc_city_borders/borders.shp")
#     subway_data_path = "data/continuous_subway_data.csv"
#     subway_data_df = pd.read_csv(subway_data_path)
#     fig, ax = plt.subplots(1, 2, figsize=(12, 10))
#     vehicle_amounts = list(vehicle_params[procedures[0]])
#     # # Collect the density levels across all dataframes
#     # all_values = pd.concat(vehicle_dfs)
#     # kde = sns.kdeplot(x=all_values["lon"], y=all_values["lat"], fill=True)
#     # kde_levels = kde.collections[0].levels / kde.collections[0].levels[-1] 

#     for i in range(2):
#         for j in range(1):
#             axs = ax[i]
#             procedure, vehicle_amount = proc_vehicle_pairs[i+j]
#             vehicle_df = vehicle_dfs[i+j]
#             # Draw city borders
#             city_borders.plot(ax=axs, color="lightgrey", alpha=0.6, label="city borders")

#             # Draw stations
#             axs.scatter(subway_data_df["LONG"], subway_data_df["LAT"], c="purple", label="station", s = 2)

#             # Draw vehicles
#             axs.scatter(vehicle_df["lon"], vehicle_df["lat"], c="green", label="vehicle", alpha=0.6, s = 8)

#             # # Dichteplot hinzufügen
#             # sns.kdeplot(
#             #     x=vehicle_df["lon"], y=vehicle_df["lat"], ax=axs, fill=True, cmap="inferno", alpha=0.8, levels=kde_levels
#             # )
#             axs.set_xlim(-74.05, -73.69)
#             axs.set_ylim(40.535, 40.92)

#             axs.legend(loc="lower right")
#             procedure = "QLRE" if vehicle_amount == 2000 else "QL"            
#             axs.set_title(f"{procedure}, {vehicle_amount} vehicles: distribution of all vehicles\nat the end of the test period in NYC")
#             axs.set_xlabel("latitude")
#             axs.set_ylabel("longitude")
#     plt.subplots_adjust(hspace=0.3)
#     figure_path = f"store/procedure_comparisons/figures"
#     if not os.path.exists(figure_path):
#         os.makedirs(figure_path)
#     plt.savefig(f"{figure_path}/vehicle_location_proc_comp.png", dpi=600)