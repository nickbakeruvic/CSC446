import numpy as np
import math
import random
import copy
import matplotlib.pyplot as plt
import pandas as pd


class Car:
    def __init__(self, id, direction, lane, arrival_time, departure_time, cardinal_direction):
        self.id = id
        self.direction = direction
        self.lane = lane
        self.arrival_time = arrival_time
        self.departure_time = departure_time
        self.cardinal_direction = cardinal_direction

    def __str__(self):
        return f"[{self.arrival_time:2.0f}s]: Car {self.id:2.0f} going {self.direction.ljust(8)} in lane {self.lane} ({self.cardinal_direction}bound)"

    def stat_print(self):
        return f"[{self.arrival_time:2.0f}s - {self.departure_time:2.0f}s]: Car {self.id:2.0f} going {self.direction.ljust(8)} in lane {self.lane} ({self.cardinal_direction}bound)"

class Sim:
    green_direction = 0
    priority_left_turn_signal = False
    time = 0
    time_on_current_light = 0
    departed_cars = []

    def __init__(self, num_lanes, num_directions, lam, arrivals_per_lane, green_light_time, left_turn_chance, right_turn_chance, priority_left_turn_time=None, right_turn_lane=False,seed=None):
        # TODO: Maybe take total time to run sim??? rather than total arrivals
        self.num_lanes = num_lanes
        self.num_directions = num_directions
        self.lam = lam
        self.arrivals_per_lane = arrivals_per_lane
        self.green_light_time = green_light_time
        self.left_turn_chance = left_turn_chance
        self.right_turn_chance = right_turn_chance
        self.priority_left_turn_time = priority_left_turn_time
        self.right_turn_lane = right_turn_lane
        self.departed_cars = []
        self.rng = np.random.default_rng(seed)

        if self.priority_left_turn_time:
            self.priority_left_turn_signal = True

        # Generate arrivals
        traffic = []
        cardinal_directions = ['North', 'South', 'East', 'West']
        for direction in range(self.num_directions):
            traffic.append([])
            for lane in range(self.num_lanes):
                traffic[-1].append(self.generate_arrivals(lane, cardinal_directions[2 * direction + 2 * lane // self.num_lanes]))

        # Process traffic
        intersection = [None] * self.num_lanes
        not_empty = lambda t: any(any(lane != [] for lane in direction) for direction in t)

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
            self.time_on_current_light = self.time_on_current_light + 1

        self.print_stats()

    def print_stats(self):

        #for car in self.departed_cars:
        #    print(car.stat_print())

        waiting_times = [car.departure_time - car.arrival_time for car in self.departed_cars]

        left_turns = sum(1 for car in self.departed_cars if car.direction == "left")
        right_turns = sum(1 for car in self.departed_cars if car.direction == "right")
        straights = sum(1 for car in self.departed_cars if car.direction == "straight")

        stats = {
          "Total cars departed": len(self.departed_cars),
          "Cars that turned left": left_turns,
          "Cars that turned right": right_turns,
          "Cars that went straight": straights,
          "Total time": self.time,
          "Throughput": len(self.departed_cars) / self.time,
          "Average waiting time": sum(waiting_times) / len(waiting_times),
          "Max waiting time": max(waiting_times)
        }

        #print(f"Total cars departed: {len(self.departed_cars)}")
        #print(f"Cars that turned left: {left_turns}")
        #print(f"Cars that turned right: {right_turns}")
        #print(f"Cars that went straight: {straights}")
        #print(f"Total time: {self.time}")
        #print(f"Throughput: {len(self.departed_cars) / self.time} cars per tick")
        #print(f"Average waiting time: {sum(waiting_times) / len(waiting_times)} ticks")
        #print(f"Max waiting time: {max(waiting_times)} ticks")

        return stats


    def handle_red_light_traffic(self, traffic, intersection):
        red_light_traffic = traffic[(self.green_direction + 1) % 2]
        for i in range(len(red_light_traffic)):
            lane = red_light_traffic[i]
            if len(lane) == 0 or self.time < lane[0].arrival_time or lane[0].direction != 'right':
                continue

            # Check if there is straight traffic going to the lane
            # this car wants to turn right into
            car = lane[0]

            # Check the opposite lane in intersection e.g. in 4 lane intersection,
            # if we're in lane 0 then intersection lane 3 will be going straight into
            # same lane we're turning in to. If we have a dedicated right turn lane,
            # move over one lane.
            lane_to_check = car.lane ^ (self.num_lanes - 1)
            if self.right_turn_lane:
                lane_to_check = lane_to_check ^ 1

            oncoming_car = intersection[lane_to_check]
            if not oncoming_car or oncoming_car.direction != 'straight':
                #print(">>>", car, "turned right at red light\n")
                car.departure_time = self.time
                self.departed_cars.append(car)
                lane.pop(0)

    def check_light(self, intersection):

        if self.priority_left_turn_time and self.time_on_current_light == self.priority_left_turn_time:
            self.priority_left_turn_signal = False
        if self.time_on_current_light == self.green_light_time:
            self.green_direction = (self.green_direction + 1) % 2

            # All cars in the intersection can go through on a yellow
            for car in intersection:
                if car:
                    car.departure_time = self.time
                    self.departed_cars.append(car)

            intersection = [None] * self.num_lanes

            # Add an extra tick for yellow light
            self.time = self.time + 1
            #print("--- Yellow light, clearing intersection ---\n")

            if self.priority_left_turn_time:
                self.priority_left_turn_signal = True

            self.time_on_current_light = 0

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
                car.departure_time = self.time
                self.departed_cars.append(car)
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
                    #print(">>>", car, "turned left\n")
                    car.departure_time = self.time
                    self.departed_cars.append(car)
                    updated_intersection[car.lane] = None

        return updated_intersection

    def update_intersection(self, traffic, intersection):
            queue = traffic[self.green_direction]
            for i in range(len(queue)):
                lane = queue[i]

                if len(lane) == 0 or self.time < lane[0].arrival_time:
                    continue

                # On left turn signal, only left turn traffic can go (and right turn
                # traffic because we have at least 2 lanes of traffic)
                if self.priority_left_turn_signal and lane[0].direction == 'straight':
                    continue

                # No cars in the intersection occupying this lane,
                # new car can come
                if intersection[i] is None:
                    intersection[i] = lane.pop(0)

            # Move traffic out of intersection
            #print(str(self.time) + f": Intersection is (Priority left turn signal is {self.priority_left_turn_signal})")
            #for car in intersection:
                #print(car)
            #print()

            return intersection

    def generate_arrivals(self, lane, cardinal_direction):
        # TODO: Generate less cars going straight? We'll generate extra num_lanes * right_turn_chance cars
        # when we have right turn lane for example (should have shorter queue in straight lane when cars going
        # to right turn lane)


        #Normalize inter-arrival times for priority lanes (e.g. divide by left/right turn chance)
        # because we're generating less cars than for straight only lanes
        normalized_lam = self.lam
        if lane % (self.num_lanes - 1) == 0 and self.right_turn_lane:
          normalized_lam /= self.right_turn_chance
        elif abs(lane - (self.num_lanes - 1) / 2) == 0.5 and self.priority_left_turn_time:
          normalized_lam /= self.left_turn_chance


        inter_arrival_times = self.rng.poisson(lam=normalized_lam, size=self.arrivals_per_lane)
        arrival_times = inter_arrival_times.cumsum().tolist()
        direction = None

        outer = (lane % (self.num_lanes - 1) == 0)
        inner = abs(lane - (self.num_lanes - 1) / 2) == 0.5

        # Outer lane with right turn lane: generate only right turn traffic
        if outer and self.right_turn_lane:
            direction = ['right' for _ in range(self.arrivals_per_lane)]

        # Outer lane with no right turn lane: generate straight traffic & right turn traffic
        elif outer and not self.right_turn_lane:
            direction = ['right' if self.rng.random() < self.right_turn_chance else 'straight' for _ in range(self.arrivals_per_lane)]

        # Inner lane with left turn lane: generate only left turn traffic
        elif inner and self.priority_left_turn_time:
            direction = ['left' for _ in range(self.arrivals_per_lane)]

        # Inner lane with no left turn lane: generate straight & left turn traffic
        elif inner and not self.priority_left_turn_time:
            direction = ['left' if self.rng.random() < self.left_turn_chance else 'straight' for _ in range(self.arrivals_per_lane)]

        # Not inner lane and not outer lane: generate only straight traffic
        elif not inner and not outer:
            direction = ['straight' for _ in range(self.arrivals_per_lane)]

        lane = [lane for _ in range(len(direction))]
        id = [i for i in range(len(direction))]

        return [Car(id[i], direction[i], lane[i], arrival_times[i], None, cardinal_direction) for i in range(len(direction))]


lams = [0.1, 0.2, 0.3, 0.4, 0.5]
left_turn_chances = [0.2, 0.3]
right_turn_chances = [0.2, 0.3]
results_1 = []
results_2 = []
results_3 = []
results_4 = []
for arrival_rate in lams:
  for left_turn_rate in left_turn_chances:
    for right_turn_rate in right_turn_chances:
      for seed in range (1, 6):
        simulate_1 = Sim(num_lanes=4, num_directions=2, lam=arrival_rate, arrivals_per_lane=10, green_light_time=10, left_turn_chance=left_turn_rate, right_turn_chance=right_turn_rate, priority_left_turn_time=None, right_turn_lane=False, seed = seed)
        simulate_2 = Sim(num_lanes=6, num_directions=2, lam=arrival_rate, arrivals_per_lane=10, green_light_time=10, left_turn_chance=left_turn_rate, right_turn_chance=right_turn_rate, priority_left_turn_time=None, right_turn_lane=True, seed = seed)
        simulate_3 = Sim(num_lanes=6, num_directions=2, lam=arrival_rate, arrivals_per_lane=10, green_light_time=10, left_turn_chance=left_turn_rate, right_turn_chance=right_turn_rate, priority_left_turn_time=3, right_turn_lane=False, seed = seed)
        simulate_4 = Sim(num_lanes=8, num_directions=2, lam=arrival_rate, arrivals_per_lane=10, green_light_time=10, left_turn_chance=left_turn_rate, right_turn_chance=right_turn_rate, priority_left_turn_time=3, right_turn_lane=True, seed = seed)
        #collect stats
        stats_1 = simulate_1.print_stats()
        stats_1.update({
                  "arrival_rate": arrival_rate,
                  "left_turn_rate": left_turn_rate,
                  "right_turn_rate": right_turn_rate
        })
        results_1.append(stats_1)
        stats_2 = simulate_2.print_stats()
        stats_2.update({
                  "arrival_rate": arrival_rate,
                  "left_turn_rate": left_turn_rate,
                  "right_turn_rate": right_turn_rate
        })
        results_2.append(stats_2)
        stats_3 = simulate_3.print_stats()
        stats_3.update({
                  "arrival_rate": arrival_rate,
                  "left_turn_rate": left_turn_rate,
                  "right_turn_rate": right_turn_rate
        })
        results_3.append(stats_3)
        stats_4 = simulate_4.print_stats()
        stats_4.update({
                  "arrival_rate": arrival_rate,
                  "left_turn_rate": left_turn_rate,
                  "right_turn_rate": right_turn_rate
        })
        results_4.append(stats_4)
        #print("Simulation Stats:")
        #for key, value in stats.items():
        #      print(f"  {key}: {value}")
        #print("-" * 50)




df_1 = pd.DataFrame(results_1)
df_2 = pd.DataFrame(results_2)
df_3 = pd.DataFrame(results_3)
df_4 = pd.DataFrame(results_4)

df_1['Sim Type'] = 'Default Intersection'
df_2['Sim Type'] = 'Extra Right Turn Lane'
df_3['Sim Type'] = 'Left Turn Signal'
df_4['Sim Type'] = 'Right Turn Lane & Left Turn Signal'


combined_df = pd.concat([df_1, df_2, df_3, df_4], ignore_index=True)
averaged_df = combined_df.groupby(['arrival_rate', 'left_turn_rate', 'right_turn_rate', 'Sim Type']).mean().reset_index()
metrics = ['Throughput', 'Average waiting time', 'Max waiting time']

for left_turn_rate in left_turn_chances:
    for right_turn_rate in right_turn_chances:
        subset = averaged_df[(averaged_df['left_turn_rate'] == left_turn_rate) & 
                             (averaged_df['right_turn_rate'] == right_turn_rate)]
        
        for metric in metrics:
            plt.figure(figsize=(10, 6))
            
            
            for sim_type, data in subset.groupby('Sim Type'):
                plt.plot(data['arrival_rate'],data[metric],marker='o',label=sim_type)
            
            plt.title(f'{metric} vs Arrival Rate\n(Left Turn Rate: {left_turn_rate}, Right Turn Rate: {right_turn_rate})')
            plt.xlabel('Arrival Rate')
            plt.ylabel(metric)
            plt.legend(title="Simulation Type", loc='upper right', framealpha = 0.5) 
            plt.grid(True)
            plt.tight_layout()
            plt.show()





# Default intersection setup
#Sim(num_lanes=4, num_directions=2, lam=0.3, arrivals_per_lane=10, green_light_time=10, left_turn_chance=0.3, right_turn_chance=0.3, priority_left_turn_time=None, right_turn_lane=False)

# Extra right turn lane
#Sim(num_lanes=6, num_directions=2, lam=0.3, arrivals_per_lane=10, green_light_time=10, left_turn_chance=0.3, right_turn_chance=0.3, priority_left_turn_time=None, right_turn_lane=True)

# Extra left turn lane & signal
#Sim(num_lanes=6, num_directions=2, lam=0.3, arrivals_per_lane=10, green_light_time=10, left_turn_chance=0.3, right_turn_chance=0.3, priority_left_turn_time=3, right_turn_lane=False)

# Extra right turn lane and extra left turn lane/signal
#Sim(num_lanes=8, num_directions=2, lam=0.3, arrivals_per_lane=10, green_light_time=10, left_turn_chance=0.3, right_turn_chance=0.3, priority_left_turn_time=3, right_turn_lane=True)