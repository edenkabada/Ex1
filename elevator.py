import sys
import json
from csv import reader, writer

UP = 1
DOWN = -1


class CallForElevator(object):
    def __init__(self, name_s, time, source, destination, value, allocated_elevator):
        self.__name = name_s
        self.__time = time
        self.__source = source
        self.__destination = destination
        self.__value = value
        self.__allocated_elevator = allocated_elevator

    def get_row(self):
        return [self.__name, self.__time, self.__source, self.__destination, self.__value, self.__allocated_elevator]

    def get_source(self):
        return self.__source

    def get_destination(self):
        return self.__destination

    def get_time(self):
        return self.__time

    def get_type(self):
        if self.__source < self.__destination:
            return UP
        return DOWN

    def allocate_elevator(self, _id):
        self.__allocated_elevator = _id


class Building(object):
    def __init__(self, min_floor, max_floor):
        self.__min_floor = min_floor
        self.__max_floor = max_floor
        self.__num_of_elevators = 0
        self.__elevators = []

    def get_elevators(self):
        return self.__elevators

    def add_elevator(self, _id, speed, min_floor, max_floor, time_open, time_close, start_t, stop_t):
        self.__num_of_elevators =+ 1
        self.__elevators.append(Elevator(_id, speed, min_floor, max_floor, time_open, time_close, start_t, stop_t))


class Elevator(object):
    def __init__(self, _id, speed, min_floor, max_floor, time_open, time_close, start_t, stop_t):
        self.__min_floor = min_floor
        self.__max_floor = max_floor
        self.__time_open = time_open
        self.__time_close = time_close
        self.__start_time = start_t
        self.__stop_time = stop_t
        self.__pos = min_floor
        self.__id = _id
        self.__speed = speed
        self.__floor_calls = []
        self.__up_queue = []
        self.__down_queue = []
        self.__state = UP
        self.__time = None

    def set_time(self, time):
        self.__time = time

    def set_state(self, state):
        self.__state = state

    def get_calls(self):
        return self.__floor_calls

    def get_up_queue(self):
        return self.__up_queue

    def get_down_queue(self):
        return self.__down_queue

    def get_state(self):
        return self.__state

    def add_to_calls(self, call):
        if call.get_source() not in self.__floor_calls:
            self.__floor_calls.append((call.get_source(), call.get_time()))
        if call.get_destination() not in self.__floor_calls:
            self.__floor_calls.append((call.get_destination(), call.get_time()))
        if call.get_type() == UP:
            self.__floor_calls.sort()
        else:
            self.__floor_calls.sort(reverse=True)

    def add_to_queue(self, call):
        if self.get_state() == UP:
            if call.get_source() not in self.__up_queue:
                self.__up_queue.append(call.get_source())
            if call.get_destination() not in self.__up_queue:
                self.__up_queue.append(call.get_destination())
            self.__up_queue.sort()

        if self.get_state() == DOWN:
            if call.get_source() not in self.__down_queue:
                self.__down_queue.append(call.get_source())
            if call.get_destination() not in self.__down_queue:
                self.__down_queue.append(call.get_destination())
            self.__down_queue.sort(reverse=True)

    def get_id(self):
        return self.__id

    def get_min_floor(self):
        return self.__min_floor

    def get_max_floor(self):
        return self.__max_floor

    def get_time_open(self):
        return self.__time_open

    def get_time_close(self):
        return self.__time_close

    def get_pos(self):
        return self.__pos

    def go_to(self, pos):
        self.__pos = pos

    def move_elevator(self):
        if not self.__floor_calls:
            if self.__up_queue or self.__down_queue:
                if not self.__up_queue:
                    self.__floor_calls.extend(self.__down_queue)
                    self.__floor_calls.sort(reverse=True)
                    self.__state = DOWN
                else:
                    self.__floor_calls.extend(self.__up_queue)
                    self.__floor_calls.sort()
                    self.__state = UP
            else:
                return
        if self.__pos == self.__floor_calls[0]:
            self.__floor_calls.pop(0)
            return
        elif self.__pos < self.__floor_calls[0]:
            self.__state = UP
        else:
            self.__state = DOWN
        self.__move_to(self.__floor_calls[0])

    def __move_to(self, pos):
        self.__time += abs(pos - self.__pos) * self.__speed + self.__time_close + self.__time_open
        self.__pos = pos


class ElevatorAlgo(object):
    def __init__(self):
        self.__building = None
        self.__calls = []
        self.__current_time = None

    def __is_call_after(self, elevator, call):
        return (call.get_time() > elevator.get_calls()[0][1]) and (call.get_time() < elevator.get_calls()[-1][1])

    def __find_closest_empty_elevator(self, call):
        min_distance = sys.maxsize
        res = None
        for el in self.__building.get_elevators():
            if not el.get_calls() and abs(el.get_pos() - call.get_source()) < min_distance:
                min_distance = abs(el.get_pos() - call.get_source())
                res = el
        return res

    def __find_elevator_suitable(self, call):
        res = None
        for el in self.__building.get_elevators():
            if el.get_calls()[0][0] <= call.get_source() and self.__is_call_after(el, call) and el.get_calls()[-1][0] >= call.get_destination():
                return el
        return res

    def __find_elevator_partial_range(self, call):
        res = None
        for el in self.__building.get_elevators():
            if el.get_state() == UP and call.get_type() == UP:
                if (call.get_source() <= el.get_calls()[0][0]) and call.get_source() >= el.get_pos():
                    return el
                else:
                    return res
            if el.get_state() == DOWN and call.get_type() == DOWN:
                if (call.get_source() >= el.get_calls()[0][0]) and call.get_source() <= el.get_pos():
                    return el
                else:
                    return res
        return res

    def __find_closest_elevator(self, call):
        min_distance = sys.maxsize
        res = None
        for el in self.__building.get_elevators():
            if abs(el.get_calls()[-1][0] - call.get_source()) < min_distance:
                min_distance = abs(el.get_calls()[-1][0] - call.get_source())
                res = el
        return res

    def __allocate_elevator_to_call(self, call):
        #if there is a close empty elevator
        allocated_elevator = self.__find_closest_empty_elevator(call)
        if allocated_elevator:
            allocated_elevator.add_to_calls(call)
            return allocated_elevator

        #if there is a elevator in range of previous calls
        allocated_elevator = self.__find_elevator_suitable(call)
        if allocated_elevator:
            allocated_elevator.add_to_calls(call)
            return allocated_elevator

        #if there is a elevator in partial range of previous calls
        allocated_elevator = self.__find_elevator_partial_range(call)
        if allocated_elevator:
            allocated_elevator.add_to_calls(call)
            return allocated_elevator

        #closest elevator that will be free
        allocated_elevator = self.__find_closest_elevator(call)
        allocated_elevator.add_to_queue(call)
        return allocated_elevator

    def create_building(self, json_file):
        with open(json_file) as jf:
            data = json.load(jf)
            self.__building = Building(data['_minFloor'], data['_maxFloor'])
            for el in data["_elevators"]:
                self.__building.add_elevator(el["_id"], el["_speed"], el["_minFloor"],
                                             el["_maxFloor"], el["_closeTime"],el["_openTime"],
                                             el["_startTime"], el["_stopTime"])

    def create_calls(self, csv_file):
        with open(csv_file, 'r') as read_obj:
            csv_reader = reader(read_obj)
            for row in csv_reader:
                self.__calls.append(CallForElevator(row[0], row[1], int(row[2]), int(row[3]), row[4], row[5]))

    def create_output(self, out_file):
        self.__calls.sort(key=lambda x: x.get_time())
        for c in self.__calls:
            el = self.__allocate_elevator_to_call(c)
            c.allocate_elevator(el.get_id())

        with open(out_file, 'w') as f:
            csv_writer = writer(f)
            for c in self.__calls:
                csv_writer.writerow(c.get_row())


if __name__ == '__main__':
    eg = ElevatorAlgo()
    eg.create_building(sys.argv[1])
    eg.create_calls(sys.argv[2])
    eg.create_output(sys.argv[3])