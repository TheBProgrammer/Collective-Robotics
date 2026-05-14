import random

class Firefly:
    def __init__(self, cycle_length=50):
        # population is scaatterd uniformly over 1x1 square
        self.x = random.uniform(0.0, 1.0)
        self.y = random.uniform(0.0, 1.0)

        # Initialize fireflies to uniformly randomly distributed clock cycles
        self.cycle_length = cycle_length
        self.clock = random.randint(0, self.cycle_length - 1)

    def is_flashing(self):
        """ Firefly flashes for L/2 timesteps"""
        return self.clock < (self.cycle_length / 2)
    
    def should_check_neighbors(self):
        """ checks neighbors in the time step AFTER it has started to flash"""
        return self.clock == 1
    
    def corrects_clock(self):
        """ corrects its clock by adding 1 """
        self.clock += 1

    def tick(self):
        # Advance the clock by 1 for the normal passage of time
        self.clock += 1
        
        # Reset the clock if it reaches the end of the cycle
        if self.clock >= self.cycle_length:
            self.clock = 0
    