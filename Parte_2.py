
"""
Agentes con DES

1. Dinamica
Se mueven en un espacio
Cada agente tiene energia -> stock
Flow: 
  - stock se recupera con el tiempo (inflow)
  - Se gasta con interacciones y movimiento

2. MBA
Agentes interactuan con otros cercanos.
Positivas donde ganan energia o pierden

3. DES
Si energia cae debajo de un umbral debe bucar
estacion de recarga, la cual es el recurso limitado
y compartido.
Agentes entran a una queue para acceder a estas

"""


import simpy
import random
import numpy as np

# Global
NUM_AGENTS = 20
WIDTH = 20
HEIGHT = 20

# DES
RECHARGE_TIME = 10
CRIT_THRESH = 10
NUM_STATIONS = 10

# 1. MBA
class Agent():
    def __init__(self, _id, energy, x0, y0, env, resource):
        self.id = _id
        self.energy = energy
        self.pos = np.array([x0,y0])
        self.env = env
        self.resource = resource
        
    def recharge_process(self):
        with self.resource.request() as req:
            yield req
            yield self.env.timeout(RECHARGE_TIME)
            self.energy = 10
            

class MBAModel():
    def __init__(self):
        self.pos = np.zeros(2)
        self.v = np.random(2)
        
# 2. System Dynamics
class DSModel():
    def __init__(
            self,
            natural,
            m_cost, 
            int_effect,
            init_energy
        ):
        # Recuperacion natural
        self.natural = natural
        # Costo de movimiento
        self.m_cost = m_cost
        # Efecto de interaccion
        self.int_effect = int_effect
        
        self.energy = init_energy

    def flow(self, dt):
        
        nat_flow = self.natural # +
        mov_flow = -self.m_cost # -
        int_flow = -self.int_effect # -
        
        self.energy += (
            self.natural
            - self.m_cost
            - self.int_flow    
        )*dt
        
# 4. Simulation

def update_state(
    env, ds_model:DSModel, mba_model, des,
    dt
):
    # 1 DS logic
    ds_model.flow(dt)
    current_energy = ds_model.energy
    pass
    

def sim_hybrid(time, dt):
    env = simpy.Enviornment()
    
    ds_model = DSModel()
    mba_model = MBAModel()
    des = simpy.Resource()
    
    update_state(env, ds_model, mba_model, des, dt)
    print("Hello world!")

    
if __name__ == "__main__":
    # Sim params
    time = 10
    dt = 10
    sim_hybrid(time, dt)
        
        
        

