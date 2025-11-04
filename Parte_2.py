
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
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Global
WIDTH = 10
HEIGHT = 10
MAX_ENERGY = 10

# DES
RECHARGE_TIME = 10
CRIT_THRESH = 2
NUM_STATIONS = 10

# DS
INIT_ENERGY = 100
NATURAL = 0.5
INT_COST = 5
MOV_EFFECT = 0.5

# MBAs
INTERACTION_RADIUS = 0.2
NUM_AGENTS = 20

# 1. MBA
class Agent():
    def __init__(self, _id, energy, x0, y0, env, resource):
        self.id = _id
        self.energy = energy
        self.pos = np.array([x0,y0])
        self.v = np.random.uniform(-5, 5, size=2)
        self.env = env
        self.resource = resource
    
    def update_pos(self, dt):
        tem_vel = self.v
        tem_pos = self.pos + self.v*dt
        for i, limit in enumerate([WIDTH, HEIGHT]):
            if tem_pos[i]<0:
                tem_pos[i] = -tem_pos[i]
                tem_vel[i] = -tem_vel[i]
            if tem_pos[i]>limit:
                tem_pos[i] = (2*limit) - tem_pos[i]
                tem_vel[i] = -tem_vel[i]
        self.v = tem_vel
        self.pos = tem_pos
        
    def recharge_process(self):
        with self.resource.request() as req:
            yield req
            yield self.env.timeout(RECHARGE_TIME)
            self.energy = MAX_ENERGY
            
class MBAModel():
    def __init__(self, env, resource, dt):
        self.agents = []
        self.env = env
        self.dt = dt
        for i in range(NUM_AGENTS):
            self.agents.append(
                Agent(
                    _id=i,
                    energy=random.random()*MAX_ENERGY,
                    x0 = random.random()*WIDTH,
                    y0 = random.random()*HEIGHT,
                    env=env,
                    resource=resource
                )
            )
    def count_interaction(self, a):
        interactions = 0
        for b in self.agents:
            if (b.id == a.id):
                continue
            if (b.pos[0] < a.pos[0]+INTERACTION_RADIUS 
                and b.pos[0] > a.pos[0]-INTERACTION_RADIUS):
                if(b.pos[1] < a.pos[1] + INTERACTION_RADIUS
                   and b.pos[1] > a.pos[1] - INTERACTION_RADIUS):
                    interactions+=1
        return interactions
                
    def update_agents(self):
        for a in self.agents:
            
            # Position Update
            a.update_pos(self.dt)
            
            # Interaction
            interaction_count = self.count_interaction(a)
            for _ in range(interaction_count):
                intensity = random.choice([-1,1]) # Effect between -1 and 1
                a.energy+=INT_COST*intensity # Just add to energy
                
            # Treshold
            if (a.energy<CRIT_THRESH):
                a.env.process(a.recharge_process())
# 2. System Dynamics
class DSModel():
    def __init__(
            self,
            init_energy,
            dt
        ):
        self.energy = init_energy
        self.dt = dt

    def flow(self):
        self.energy += (
            NATURAL
            - MOV_EFFECT
            - INT_COST    
        )*self.dt

# 0. Metric colector

class Metrics():
    def __init__(self,dt):
        self.dt = dt
        self.time = []
        self.energies = []
        self.positions = []
        self.agent_energies = []
    
    def save(self, env, mba_model):
        self.time.append(env.now)
        energies = [a.energy for a in mba_model.agents]
        self.agent_energies.append(energies)
        self.energies.append(np.mean(energies))
        self.positions.append([a.pos for a in mba_model.agents])
        self.ani = None
        
    def show(self):
        plt.plot(self.time, self.energies)
        plt.show()
        
    def animate(self):
        n_steps = len(self.positions)
        fig, ax = plt.subplots()
        
        cmap = plt.cm.plasma  
        
        scat = ax.scatter([], [], s=30, c=[], cmap=cmap, vmin=0, vmax=MAX_ENERGY)
        time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes)

        ax.set_xlim(0, WIDTH)
        ax.set_ylim(0, HEIGHT)
        ax.set_title("Agent Simulation")

        cbar = plt.colorbar(scat, ax=ax)
        cbar.set_label("Energy")
        def init():
            scat.set_offsets(self.positions)
            scat.set_array(self.agent_energies)
            time_text.set_text('')
            return scat, time_text

        def update(frame):
            scat.set_offsets(self.positions[frame])
            scat.set_array(self.agent_energies[frame])
            time_text.set_text(f't = {frame*dt}')
            return scat, time_text

        self.ani = FuncAnimation(fig, update, frames=n_steps, init_func=init, blit=False, interval=10)
        plt.show()
        
# 4. Simulation

def update_state(
    env, ds_model:DSModel, mba_model, des
):
    # 1 DS logic
    ds_model.flow()
    global_energy = ds_model.energy
    mba_model.update_agents()
    
    

def sim_hybrid(env, time, metrics,dt):
    
    ds_model = DSModel(
        init_energy=INIT_ENERGY,
        dt=dt, 
    )
    des = simpy.Resource(env, NUM_STATIONS)
    mba_model = MBAModel(
        env,
        des,
        dt
    )
    while(env.now < time):
        print
        update_state(env, ds_model, mba_model, des)
        metrics.save(env, mba_model)
        yield env.timeout(dt)
if __name__ == "__main__":
    # Sim params
    time = 10
    dt = 0.01
    
    metrics = Metrics(dt)
    env = simpy.Environment()
    
    env.process(
        sim_hybrid(env, time, metrics, dt)
    )
    env.run()
    metrics.show()
    
        
        
        

