import uuid


class IdProvider:
    def __init__(self) -> None:
        self._current_id = 0
        self._uuid_gen = uuid
    
    def get_id(self):
        current_id = self._current_id
        self._current_id += 1
        return current_id
    
    def get_uuid(self):
        return self._uuid_gen.uuid4()