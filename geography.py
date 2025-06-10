import csv
import utils
import numpy as np


class Airport:

    def __init__(self, name, position, country, type):
        self.name       = name
        self.position   = position
        self.country    = country
        self.type       = type


class AirportManager:

    def __init__(self, airport_csv, filter_types=["large_airport"]):
        
        # Parse all airports
        self.airports   = []

        file            = open(airport_csv, "r")
        reader          = csv.reader(file)

        # Skip header
        columns         = next(reader)
        print("\n".join(["{}: {}".format(i, c) for i, c in enumerate(columns)]))

        for line in reader:
            airport_type = line[2]
            if not airport_type in filter_types:
                continue
            lat, lon    = float(line[4]), float(line[5])
            x, y        = utils.convert_lat_lon(lat, lon)
            airport     = Airport(line[3], (x, y), line[8], airport_type,)
            self.airports.append(airport)
        print("Found '{}' airports!".format(len(self.airports)))



class Mission:

    def __init__(self, target: Airport, threshold_distance: float):
        self.target             = target
        self.threshold_distance = threshold_distance


    def check_distance(self, pos):
        #print(pos, self.target.position)
        x1, y1  = pos
        x2, y2  = self.target.position
        dist    = np.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)
        return dist < self.threshold_distance


class MissionManager:

    def __init__(self, configs):
        
        self.configs            = configs
        self.airport_manager    = AirportManager(configs.get("airport_file"))
        self.mission            = None

    def get_airports(self):
        return self.airport_manager.airports
    
    def new_mission(self):
        rand_index              = np.random.randint(len(self.airport_manager.airports))
        self.mission            = Mission(self.airport_manager.airports[rand_index], self.configs.getfloat("target_radius"))
        return self.mission

        
