from __future__ import annotations
from program.vehicle.vehicle_job import VehicleJob
from program.location.location import Location
from program.utils import IdProvider

ID_PROVIDER = IdProvider()

class Vehicle:

    def __init__(self, start_position: Location, id: int = None) -> None:
        self.id = id if id != None else ID_PROVIDER.get_id()
        self.current_position = start_position
        self.job: VehicleJob = None
        # Time that passed since vehicles last job
        self.idle_time = 0

    def is_occupied(self) -> bool:
        return self.job != None

    def set_new_job(self, total_driving_time: int, passenger_pickup_time: int, pickup_position: Location, new_position: Location) -> None:
        self.job = VehicleJob.of_trip(total_driving_time, passenger_pickup_time, self.current_position, pickup_position, new_position)
    
    def set_new_relocation_job(self, total_driving_time: int, new_position: Location) -> None:
        self.job = VehicleJob.of_relocation(total_driving_time, self.current_position, new_position)

    # Duration in seconds
    def update_job_status(self, duration: int) -> None:
        if self.job == None:
            self.idle_time += duration
            return

        self.idle_time = 0
        if self.job.open_trip_time - duration < 0:
            # Job is finished by next interval
            self.current_position = self.job.final_position
            self.job = None
        else:
            self.job.open_trip_time -= duration
            self.current_position = self.job.get_next_position()
