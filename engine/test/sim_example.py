from sim.simulator import Simulator
from sim.event.event import TimedEventImpl


if __name__ == '__main__':
    simulator = Simulator()

    def execute(event, _):
        print(simulator.sim_time)
        event.sim_time += 1
        simulator.event_queue << event
    simulator.event_queue << TimedEventImpl(0.0, execute)

    simulator.run()
