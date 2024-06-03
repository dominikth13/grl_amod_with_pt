from multiprocessing.managers import DictProxy
from program.order.order import Order
from program.order.route import Route

def dispatch_order(order: Order) -> Order:
    order.dispatch()
    return order