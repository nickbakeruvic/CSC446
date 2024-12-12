import numpy as np
import random
import copy


class Car:
    def __init__(self, id, direction, lane, arrival_time, departure_time, cardinal_direction):
        self.id = id
        self.direction = direction
        self.lane = lane
        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.cardinal_direction = cardinal_direction

    def __str__(self):
        return f"[{self.arrival_time:3.0f}s]: Car {self.id:3.0f} going {self.direction.ljust(8)} in lane {self.lane} ({self.cardinal_direction}bound)"

class Sim:

    green_direction = 0

    num_lanes, num_directions = 4, 2
    time = 0
    
    # TODO: Remove
    LAMBDA = 1
    ARRIVALS_PER_LANE = 10
    GREEN_LIGHT_TIME = 10

    def __init__(self):
        # TODO: take rate of traffic etc.
        
        # Generate arrivals
        traffic = []
        cardinal_directions = ['North', 'South', 'East', 'West']
        for direction in range(self.num_directions):
            traffic.append([])
            for lane in range(self.num_lanes):
                traffic[-1].append(self.generate_arrivals(self.LAMBDA, self.ARRIVALS_PER_LANE, lane, cardinal_directions[(self.num_lanes * direction + lane) // 2]))

        # Process traffic
        intersection = [None, None, None, None]
        not_empty = lambda t: any(any(lane != [] for lane in direction) for direction in t)

        # TODO: Implement right turn slip lane
        # TODO: Implement left turn signal
        while not_empty(traffic):
            
            # Move traffic from lanes into intersection
            intersection = self.update_intersection(traffic, intersection)

            # Handle right turns on red light
            self.handle_red_light_traffic(traffic, intersection)

            # Move traffic through intersection
            intersection = self.process_intersection_traffic(intersection)

            # Change light if necessary
            intersection = self.check_light(intersection)

            self.time = self.time + 1

    def handle_red_light_traffic(self, traffic, intersection):
        red_light_traffic = traffic[(self.green_direction + 1) % 2] 
        for i in range(len(red_light_traffic)):
            lane = red_light_traffic[i]
            if len(lane) == 0 or self.time < lane[0].arrival_time or lane[0].direction != 'right':
                continue

            # Check if there is straight traffic going to the lane
            # this car wants to turn right into
            car = lane[0]
            oncoming_car = intersection[car.lane] 
            if not oncoming_car or oncoming_car.direction != 'straight':
                print(">>>", car, "turned right at red light\n")
                lane.pop(0)

    def check_light(self, intersection):
        if self.time % self.GREEN_LIGHT_TIME == 0 and self.time != 0:
            self.green_direction = (self.green_direction + 1) % 2

            # All cars in the intersection can go through on a yellow
            intersection = [None, None, None, None]

            # Add an extra tick for yellow light
            self.time = self.time + 1
            print("--- Yellow light, clearing intersection ---\n")

        return intersection

    def process_intersection_traffic(self, intersection):
        # We need to copy intersection without reference
        # so we can move cars through without losing track
        # of them
        updated_intersection = copy.deepcopy(intersection)

        for car in intersection:
            if not car:
                continue

            # Car can pass through intersection
            if car.direction == 'straight' or car.direction == 'right':
                updated_intersection[car.lane] = None

            # Check left turn eligibility
            else:
                oncoming_straight_car = False
                for other_car in intersection:
                    # Check if car is oncoming
                    if other_car and other_car.lane // 2 != car.lane // 2:
                        if other_car.direction == 'straight':
                            oncoming_straight_car = True
                            break

                if not oncoming_straight_car:
                    print(">>>", car, "turned left\n")
                    updated_intersection[car.lane] = None

        return updated_intersection

    def update_intersection(self, traffic, intersection):
            queue = traffic[self.green_direction]
            for i in range(len(queue)):
                lane = queue[i]

                if len(lane) == 0 or self.time < lane[0].arrival_time:
                    continue
        
                # No cars in the intersection occupying this lane,
                # new car can come
                if intersection[i] is None:
                    intersection[i] = lane.pop(0)

            # Move traffic out of intersection
            print(str(self.time) + ": Intersection is")
            for car in intersection:
                print(car)
            print()

            return intersection

    def generate_arrivals(self, lam, size, lane, cardinal_direction, rng = np.random.default_rng(seed=0)):
        inter_arrival_times = rng.poisson(lam=lam, size=size)
        arrival_times = inter_arrival_times.cumsum().tolist()
        direction = None

        outer = (lane % (self.num_lanes - 1) == 0)
        if outer:
            direction = ['right' if random.random() < 0.3 else 'straight' for _ in range(size)]
        else:
            direction = ['left' if random.random() < 0.2 else 'straight' for _ in range(size)]

        lane = [lane for _ in range(size)]
        id = [i for i in range(size)]

        return [Car(id[i], direction[i], lane[i], arrival_times[i], None, cardinal_direction) for i in range(len(id))]

# TODO: run multiple sims, compare results
Sim()