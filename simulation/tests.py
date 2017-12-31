import unittest
from plant import PlantEnv


class TestPlantEnv(unittest.TestCase):

    def test_action_state_dimensions(self):
        env = PlantEnv()
        self.assertEqual(3, len(env.action_space.sample()))
        self.assertEquals(6, len(env.observation_space.sample()))

    def test_dark(self):
        self.assertTrue(PlantEnv.is_dark(0))
        self.assertFalse(PlantEnv.is_dark(60*12))

    def test_random_actions(self):
        state_variables = ["soil_humidity", "light", "temperature", "air_humidity", "water_level", "time"]

        env = PlantEnv()
        for i in range(10):
            a = env.action_space.sample()
            print zip(a, ["pump", "led", "condenser"])
            s, r, finished, _ = env.step(a)
            print zip(state_variables, s)


if __name__ == '__main__':
    unittest.main()
