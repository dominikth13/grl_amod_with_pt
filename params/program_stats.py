import csv
import os
from params.program_params import ProgramStage


class ProgramStats:
    SUM_OF_TIMESAFE = 0

    # Runtime in seconds
    RUNTIME = {
        ProgramStage.ORDER_DISPATCHING: 0,
        ProgramStage.ROUTE_GENERATION: 0,
        ProgramStage.VEHICLE_ACTION_PAIRING: 0,
        ProgramStage.VOM: 0,
        ProgramStage.RE: 0,
        ProgramStage.SIM_UPDATE: 0,
        ProgramStage.VALUE_FUNC_UPDATE: 0
    }

    def export_to_csv() -> None:
        existing_runtime = {
            1: 0,
            2: 0,
            3: 0,
            4: 0,
            5: 0,
            6: 0,
            7: 0
        }
        if os.path.exists("data/runtime.csv"):
            with open("data/runtime.csv", mode="r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    existing_runtime[int(row["stage"])] += float(row["runtime"])
            os.remove("data/runtime.csv")
        
        with open("data/runtime.csv", mode="w") as file:
            writer = csv.writer(file)
            writer.writerow(["stage", "runtime"])
            for stage in ProgramStats.RUNTIME:
                writer.writerow([stage.value, existing_runtime[stage.value] + ProgramStats.RUNTIME[stage]])
                ProgramStats.RUNTIME[stage] = 0
