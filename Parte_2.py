
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
RECHARGE_TIME = 1
CRIT_THRESH = 2
NUM_STATIONS = 1

# DS
INIT_ENERGY = 10
NATURAL = 100
INT_COST = 55
MOV_EFFECT = 1

# MBAs
INTERACTION_RADIUS = 2
NUM_AGENTS = 25

# 1. MBA
class Agent():
    def __init__(self, _id, energy, x0, y0, env, resource):
        self.id = _id
        self.is_recharging = False
        self.energy = energy
        self.pos = np.array([x0,y0])
        self.v = np.random.uniform(-5, 5, size=2)
        self.env = env
        self.resource = resource
    
    def update_pos(self, dt):
        if self.is_recharging:
            return
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
    
    def update_ds(self, dt, neighbors):
        if self.is_recharging:
            return
        movement_cost = MOV_EFFECT * np.linalg.norm(self.v)
        
        interaction_effect = neighbors* INT_COST
        
        dE = (NATURAL - interaction_effect - movement_cost) * dt
        next_e = self.energy + dE*dt
        if next_e<0:
            self.energy = 0
        if next_e>MAX_ENERGY:
            self.energy = MAX_ENERGY
        self.energy +=dE*dt

           
    def recharge_process(self):
        self.is_recharging = True
        with self.resource.request() as req:
            yield req
            yield self.env.timeout(RECHARGE_TIME)
            self.energy = MAX_ENERGY
        self.is_recharging = False
class MBAModel():
    def __init__(self, env, init_energy, resource, dt):
        self.agents = []
        self.env = env
        self.dt = dt
        for i in range(NUM_AGENTS):
            self.agents.append(
                Agent(
                    _id=i,
                    energy=init_energy,
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
            # 1. Update ds
            neighbors = self.count_interaction(a)
            a.update_ds(dt, neighbors)
            
            # Position Update
            a.update_pos(self.dt)
            
            # Treshold
            if (not a.is_recharging and a.energy<CRIT_THRESH):
                a.env.process(a.recharge_process())

# Recharge
class MonitoredResource(simpy.Resource):
    def __init__(self, env, capacity):
        super().__init__(env, capacity)
        self.total_uses = 0 

    def request(self, *args, **kwargs):
        req = super().request(*args, **kwargs)
        return req

    def release(self, *args, **kwargs):
        self.total_uses += 1
        return super().release(*args, **kwargs)
# 0. Metric colector
class Metrics():
    def __init__(self,dt):
        self.crit_agents = []
        self.total_uses = 0
        self.enqueued = []
        self.des_use = []
        self.dt = dt
        self.time = []
        self.energies = []
        self.positions = []
        self.agent_energies = []
    
    def save(self, env, mba_model, des):
        self.enqueued.append(len(des.queue))
        self.des_use.append(len(des.users))
        
        self.time.append(env.now)
        energies = [a.energy for a in mba_model.agents]
        
        crit_amount = 0
        for e in energies:
            if e<CRIT_THRESH:
                crit_amount+=1
        self.crit_agents.append(
            crit_amount
        )
        
        self.agent_energies.append(energies)
        self.energies.append(np.mean(energies))
        self.positions.append([a.pos for a in mba_model.agents])
        self.ani = None
        
    def show(self):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

        # --- Resource behaviour --- #
        fig.suptitle(f"DES limited Resource Behaviour\nTotal Resource uses: {self.total_uses}")
        ax1.set_title("Resource Queue")
        ax1.plot(self.time, self.des_use, label="Resource Usage", color='g')
        ax1.set_ylabel("Resource Count")
        ax1.legend()
        ax2.set_title("Agent Usage")
        ax2.plot(self.time, self.enqueued, label="Enqueued Agents", color='r')
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Agent Count")
        ax2.legend()
        plt.tight_layout()
        plt.show()
        
        # --- Agents at Critical Energy levels --- #
        plt.plot(self.time, self.crit_agents)
        plt.title("Number of agents at critical energy levels")
        plt.xlabel("Time")
        plt.ylabel("Agent Count")
        plt.tight_layout()
        plt.show()
        
        # --- Mean Energy levels --- #
        plt.plot(self.time, self.energies)
        plt.title("Mean energy levels")
        plt.xlabel("Time")
        plt.ylabel("Energy")
        plt.tight_layout()
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
        

    
def sim_hybrid(env, time, metrics,dt):
    des = MonitoredResource(env, NUM_STATIONS)
    mba_model = MBAModel(
        env,
        INIT_ENERGY,
        des,
        dt
    )
    while(env.now < time):
        print
        mba_model.update_agents()
        metrics.save(env, mba_model, des)
        yield env.timeout(dt)
    
    metrics.total_uses = des.total_uses
if __name__ == "__main__":
    # Sim params
    time = 20
    dt = 0.01
    
    metrics = Metrics(dt)
    env = simpy.Environment()
    
    env.process(
        sim_hybrid(env, time, metrics, dt)
    )
    env.run()
    # metrics.animate()
    metrics.show()
    
        
        
        

