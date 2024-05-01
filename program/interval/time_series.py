from __future__ import annotations
from program.interval.grid_interval import GridInterval
from program.interval.time import Time
from program.utils import IdProvider
from params.program_params import ProgramParams

ID_PROVIDER = IdProvider()

class TimeSeries:
    _time_series = None

    def get_instance() -> TimeSeries:
        if TimeSeries._time_series == None:
            TimeSeries._time_series = TimeSeries(Time(0, 0, 0), Time(23, 59, 59), ProgramParams.GRID_INTERVAL_UPDATE_RATE)
        return TimeSeries._time_series

    def __init__(self, start: Time, end: Time, intervalLengthInSeconds: int) -> None:
        self.start_time = start
        self.end_time = end
        self.interval_by_id: dict[int, GridInterval] = {}
        self.intervals: list[GridInterval] = []

        # start, end, interval length are all in second
        start_seconds = start.to_total_seconds()
        end_seconds = end.to_total_seconds()
        
        for current_seconds in range(start_seconds, end_seconds + 1, intervalLengthInSeconds):
            interval_start = Time.of_total_seconds(current_seconds)
            interval_end = Time.of_total_seconds(current_seconds + intervalLengthInSeconds - 1)
            interval = GridInterval(interval_start, interval_end)
            self.interval_by_id[interval.id] = interval
            self.intervals.append(interval)

    def find_interval(self, time: Time) -> GridInterval:
        low = 0
        high = len(self.intervals) - 1
        mid = 0

        interval = None
        while low <= high:
            mid = (high + low) // 2

            if self.intervals[mid].start.is_before(time):
                if self.intervals[mid].end.is_after(time):
                    interval = self.intervals[mid]
                    break
                else:
                    low = mid + 1
            elif self.intervals[mid].end.is_before(time):
                low = mid + 1
            else:
                high = mid - 1

        if interval == None:
            raise Exception(f"Interval to time {time} not found")

        return interval
    
    def get_next_interval(self, current_interval: GridInterval) -> GridInterval:
        if len(self.interval_by_id) == current_interval.id + 1:
            return None
        return self.interval_by_id[current_interval.id + 1]