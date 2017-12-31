import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import random
from datetime import datetime, date, time, timedelta

class PlantEnv(gym.Env):
    """
        An environment simulating plant growing. We observer state of sensors every 1 minute
        and can make one action at a time.

        We observe:
        1. soil humidity
        2. light intensity
        3. air temperature
        4. air humidity
        5. amount of water in the tank
        6. time of the day

        We can act:
        1. enable water pump for 1 second
        2. enable/disable LED lights
        3. enable/disable water condenser

        Rewards:
        Rewards depend on soil humidity wrt time, and light intensity wrt time.
        Each energy required action such as enable water pump or LED or water condensation gives small negative
        reward, so we try to optimize also energy for plant growing.
    """

    # Constants
    punishment_per_action = np.array([-0.01, -0.01, -0.1])  # pump, LED, condenser
    water_amount_per_action = 0.01  # in liters
    water_condens_per_minute = 0.0001

    # some relative constants that we expect from sensors
    _soil_humidity_sensor_range = (0, 100)  # 0-dry, 100-water
    _light_sensor_range = (0, 100)  # 0-darkness, 100-next to 60W lamp
    _air_temperature_sensor_range = (-50, 100)  # air temperature in Celsius
    _air_humidity_sensor_range = (0, 100)  # air humidity in percentage
    _amount_water_sensor_range = (0, 1)  # amount of water in litters
    _time_sensor = (0, 100000)  # minutes since growing started

    _sensor_ranges = [_soil_humidity_sensor_range, _light_sensor_range, _air_temperature_sensor_range,
                      _air_humidity_sensor_range, _amount_water_sensor_range, _time_sensor]

    def __init__(self):

        self.viewer = None

        self.low = [sensor_range[0] for sensor_range in self._sensor_ranges]
        self.high = [sensor_range[0] for sensor_range in self._sensor_ranges]

        self.action_space = spaces.MultiBinary(3)  # 3dimensional. Enable water pump, enable LED, enable condenser
        self.observation_space = spaces.Box(np.array(self.low), np.array(self.high))
        self._seed()
        self.reset()

    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]

    def _step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid" % (action, type(action))

        action_water_pump, action_led_lights, action_condenser = action
        soil_humidity, light, temperature, air_humidity, water_level, time = self.state

        # Simulate the water and other states first.
        soil_humidity = max(0, soil_humidity - 0.01)  # in simulation humidity decreases by 0.1 every minute

        if action_water_pump and water_level > 0:  # we have water to spend
            amount_to_spil = min(water_level, self.water_amount_per_action)
            print "will spill", amount_to_spil
            water_level = water_level-amount_to_spil
            soil_humidity = min(100, soil_humidity + amount_to_spil*100)


        temperature = max(
            min(self._air_temperature_sensor_range[0], temperature+random.normalvariate(0, 1)),
            self._air_temperature_sensor_range[1])

        air_humidity = max(
            min(self._air_humidity_sensor_range[0], air_humidity+random.normalvariate(0, 1)),
            self._air_humidity_sensor_range[1]
        )

        time += 1
        if action_condenser == 1:
            water_level += self.water_condens_per_minute

        if PlantEnv.is_dark(time):
            light = 20 if action_led_lights == 1 else 10
        else:
            light = 55 if action_led_lights == 1 else 50

        #sum up the small negative rewards first
        reward = np.dot(np.array([action_water_pump, action_led_lights, action_condenser]), self.punishment_per_action)

        #reward for light
        if light < 15:
            reward -= 10
        elif light > 30:
            reward += 10

        #reward for watering
        reward -= abs(soil_humidity - 50)
        self.state = np.array([soil_humidity, light, temperature, air_humidity, water_level, time])
        return self.state, reward, False, {}

    @classmethod
    def is_dark(cls, minutes_since_experiment):
        eva_birthday = datetime.combine(date(2018, 01, 01), time(23, 30))
        current_time = eva_birthday + timedelta(minutes=minutes_since_experiment)
        return current_time.hour < 6 or current_time.hour > 18

    def _reset(self):
        """Return initial state"""
        self.state = self.np_random.uniform(low=self.low, high=self.high)
        return self.state
