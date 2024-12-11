import numpy as np
import random
import copy

# Indexing tuples generated by generate_arrivals
TIME, DIRECTION, LANE = 0, 1, 2

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
        for direction in range(self.num_directions):
            traffic.append([])
            for lane in range(self.num_lanes):
                traffic[-1].append(self.generate_arrivals(self.LAMBDA, self.ARRIVALS_PER_LANE, lane))

        # Process traffic
        intersection = [None, None, None, None]
        not_empty = lambda t: any(any(lane != [] for lane in direction) for direction in t)

        # TODO: Implement right turn slip lane
        # TODO: Implement left turn signal
        # TODO: Handle right turn on red light
        while not_empty(traffic):
            
            # Move traffic from lanes into intersection
            queue = traffic[self.green_direction]
            for i in range(len(queue)):
                lane = queue[i]
                if len(lane) == 0 or self.time < lane[0][TIME]:
                    continue
        
                # No cars in intersection, new car can come
                if intersection[i] is None:
                    intersection[i] = lane.pop(0)

            # Move traffic out of intersection
            print(str(self.time) + ": Intersection =", intersection)
            updated_intersection = copy.deepcopy(intersection)
            for car in intersection:
                if not car:
                    continue

                lane = car[LANE]
                
                # Car can pass through intersection
                if car[DIRECTION] == 'straight' or car[DIRECTION] == 'right':
                    updated_intersection[lane] = None

                # Check left turn eligibility
                else:
                    oncoming_straight_car = False
                    for other_car in intersection:
                        # Check if car is oncoming
                        if other_car and other_car[LANE] % 2 != car[LANE] % 2:
                            if other_car[DIRECTION] == 'straight':
                                oncoming_straight_car = True
                                break
                    
                    if not oncoming_straight_car:
                        print(">>>", car, "turned left\n")
                        updated_intersection[lane] = None

            intersection = copy.deepcopy(updated_intersection)

            # Change light
            if self.time % self.GREEN_LIGHT_TIME == 0 and self.time != 0:
                self.green_direction = (self.green_direction + 1) % 2
                
                # All cars in the intersection can go through on a yellow
                intersection = [None, None, None, None]
                
                # Add an extra tick for yellow light
                self.time = self.time + 1
                print("--- Yellow light, clearing intersection ---\n")
            
            self.time = self.time + 1

    def generate_arrivals(self, lam, size, lane, rng = np.random.default_rng()):
        inter_arrival_times = rng.poisson(lam=lam, size=size)
        arrival_times = inter_arrival_times.cumsum().tolist()
        direction = None

        outer = lane % 2 == 1
        if outer:
            direction = ['right' if random.random() < 0.3 else 'straight' for _ in range(size)]
        else:
            direction = ['left' if random.random() < 0.2 else 'straight' for _ in range(size)]

        lane = [lane for _ in range(size)]
        id = [i for i in range(size)]

        cars = list(zip(arrival_times, direction, lane, id)) 
        return cars

# TODO: run multiple sims, compare results
Sim()