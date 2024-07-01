class ConcurrencyParams:
    AMOUNT_OF_PROCESSES = 8
    FEATURE_ORDER_DISPATCHING_CONCURRENT = False
    FEATURE_ROUTE_CALCULATION_CONCURRENT = False
    FEATURE_BEST_ACTION_CALCULATION_CONCURRENT = False

    def set_member(member: str, value):
        if member == "AMOUNT_OF_PROCESSES":
            ConcurrencyParams.AMOUNT_OF_PROCESSES = int(value)
        elif member == "FEATURE_ORDER_DISPATCHING_CONCURRENT":
            ConcurrencyParams.FEATURE_ORDER_DISPATCHING_CONCURRENT = bool(value)
        elif member == "FEATURE_ROUTE_CALCULATION_CONCURRENT":
            ConcurrencyParams.FEATURE_ROUTE_CALCULATION_CONCURRENT = bool(value)
        elif member == "FEATURE_BEST_ACTION_CALCULATION_CONCURRENT":
            ConcurrencyParams.FEATURE_BEST_ACTION_CALCULATION_CONCURRENT = bool(value)
        else:
            raise Exception(f"No parameter found with name {member}")