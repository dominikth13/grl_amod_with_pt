import os
from params.program_params import Mode, ProgramParams

# Run this to set the parameters for analysis
def set_params():
    # Set program params
    ProgramParams.EXECUTION_MODE = Mode.GRAPH_REINFORCEMENT_LEARNING
    ProgramParams.MAX_IDLING_TIME = 300
    ProgramParams.DISCOUNT_RATE = 0.95
    ProgramParams.LS = 60
    ProgramParams.LEARNING_RATE = 0.01
    ProgramParams.IDLING_COST = 5
    ProgramParams.AMOUNT_OF_VEHICLES = 2000
    ProgramParams.RELOCATION_RADIUS = 10000
    ProgramParams.DIRECT_TRIP_DISCOUNT_FACTOR = 0.5
    ProgramParams.MAIN_AND_TARGET_NET_SYNC_ITERATIONS = 60

# Run this to get the parameter and its values for the comparison
def get_comparison_values() -> tuple[str, list]:
    # Change parameter here
    parameter = "IDLING_COST"
    values = [1, 3, 5, 10, 30]
    def cast(value):
        return float(value)
    return (parameter, list(map(cast, values)))

def get_multi_comparison_values() -> list[dict]:
    return [
        {
            "RELOCATION_RADIUS": 4000
        },
                {
            "RELOCATION_RADIUS": 5000
        },
        {
            "RELOCATION_RADIUS": 6000
        }
    ]

def get_all_multi_comparision_values() -> list[dict]:
    comparison_values = find_relevant_multi_paths(5000)
    return comparison_values
    

def find_relevant_multi_paths(amount_of_vehicles: int):
    relevant_combinations = []
    relevant_combinations.append({"AMOUNT_OF_VEHICLES": amount_of_vehicles})
    
    # Walk through the directory structure
    for root, dirs, files in os.walk("store/grl"):
        # Split the path into components
        path_components = root.split(os.sep)[2:]
        
        # Check if the path has the correct structure
        if len(path_components) == 9:
            mit, dr, ls, lr, idling_cost, aov, re_radius, direct_discount, main_target_sync = path_components[-9:]
            
            if (amount_of_vehicles == 2000 and aov == "_") or (aov != "_" and amount_of_vehicles == int(aov)):
                changes_dict = {"AMOUNT_OF_VEHICLES": 2000 if aov == "_" else int(aov)}
                changes_count = 0
                changes_sensitivity_analysis = False
                if mit != "_":
                    changes_count += 1
                    changes_dict["MAX_IDLING_TIME"] = int(mit)
                    if changes_dict["MAX_IDLING_TIME"] in [60,180,420,600]:
                        changes_sensitivity_analysis = True
                if dr != "_":
                    changes_count += 1
                    changes_dict["DISCOUNT_RATE"] = float(dr)
                    if changes_dict["DISCOUNT_RATE"] in [0.85,0.9,0.99,0.999]:
                        changes_sensitivity_analysis = True
                if ls != "_":
                    changes_count += 1
                    changes_dict["LS"] = float(ls)
                    if changes_dict["LS"] in [1.0,30.0,120.0,300.0]:
                        changes_sensitivity_analysis = True
                if lr != "_":
                    changes_count += 1
                    changes_dict["LEARNING_RATE"] = float(lr)
                    if changes_dict["LEARNING_RATE"] in [0.001,0.005,0.05,0.1]:
                        changes_sensitivity_analysis = True
                if idling_cost != "_":
                    changes_count += 1
                    changes_dict["IDLING_COST"] = float(idling_cost)
                    if changes_dict["IDLING_COST"] in [1.0,3.0,10.0,30.0]:
                        changes_sensitivity_analysis = True
                if re_radius != "_":
                    changes_count += 1
                    changes_dict["RELOCATION_RADIUS"] = int(re_radius)
                    if changes_dict["RELOCATION_RADIUS"] in [1000,3000,15000]:
                        changes_sensitivity_analysis = True
                if direct_discount != "_":
                    changes_count += 1
                    changes_dict["DIRECT_TRIP_DISCOUNT_FACTOR"] = float(direct_discount)
                    if changes_dict["DIRECT_TRIP_DISCOUNT_FACTOR"] in [0.2,0.4,0.6,0.8]:
                        changes_sensitivity_analysis = True
                if main_target_sync != "_":
                    changes_count += 1
                    changes_dict["MAIN_AND_TARGET_NET_SYNC_ITERATIONS"] = int(main_target_sync)
                    if changes_dict["MAIN_AND_TARGET_NET_SYNC_ITERATIONS"] in [1,30,120,240]:
                        changes_sensitivity_analysis = True
                
                # Check if at least two of A, B, or D are changed
                if changes_count >= 2 or (changes_count == 1 and not changes_sensitivity_analysis):
                    relevant_combinations.append(changes_dict)               
    
    return relevant_combinations