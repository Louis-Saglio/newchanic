from time import time

from newchanic.graphical_engine import GraphicalEngine2D
from newchanic.laws import Gravity

if __name__ == "__main__":

    def main():
        engine = GraphicalEngine2D(
            graphical_options={},
            particle_number=100,
            force_generators=(Gravity(),),
            # arbitrary_laws=(Merge(),)
        )
        start = time()
        # turn_number = engine.run()
        turn_number = engine.run_multiprocess(8)
        print(f"{round((time() - start) / turn_number, 3)} seconds by turn")

    main()
