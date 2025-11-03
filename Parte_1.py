import random
import statistics
from dataclasses import dataclass
from typing import Generator, Any

import simpy

@dataclass
class Config:
    NUM_RECEPCIONISTAS: int = 1
    NUM_MEDICOS: int = 2
    TIEMPO_REGISTRO_PROMEDIO: float = 2.0  # min
    TIEMPO_CONSULTA_PROMEDIO: float = 7.0  # min
    TASA_LLEGADA_PACIENTES: float = 5.0    # promedio 1 cada 5 min
    TIEMPO_SIMULACION: float = 120.0       # min
    SEED: int = 42
    TRACE: bool = True

class ClinicaDES:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        random.seed(cfg.SEED)
        self.env = simpy.Environment()
        self.recepcionistas = simpy.Resource(self.env, capacity=cfg.NUM_RECEPCIONISTAS)
        self.medicos = simpy.Resource(self.env, capacity=cfg.NUM_MEDICOS)
        # Métricas
        self.tiempos_totales = []
        self.tiempos_espera_registro = []
        self.tiempos_espera_consulta = []
        self.pacientes_completados = 0

    def paciente(self, nombre: str) -> Generator[Any, Any, None]:
        llegada = self.env.now
        if self.cfg.TRACE:
            print(f"[{self.env.now:6.2f}] Llega {nombre}")

        # --- Registro ---
        t_solicita_reg = self.env.now
        with self.recepcionistas.request() as req_reg:
            yield req_reg
            espera_reg = self.env.now - t_solicita_reg
            self.tiempos_espera_registro.append(espera_reg)
            if self.cfg.TRACE:
                print(f"[{self.env.now:6.2f}] {nombre} inicia REGISTRO (esperó {espera_reg:.2f} min)")
            dur_reg = random.expovariate(1.0 / self.cfg.TIEMPO_REGISTRO_PROMEDIO)
            yield self.env.timeout(dur_reg)
            if self.cfg.TRACE:
                print(f"[{self.env.now:6.2f}] {nombre} termina REGISTRO (duró {dur_reg:.2f} min)")

        # --- Consulta ---
        t_solicita_cons = self.env.now
        with self.medicos.request() as req_med:
            yield req_med
            espera_cons = self.env.now - t_solicita_cons
            self.tiempos_espera_consulta.append(espera_cons)
            if self.cfg.TRACE:
                print(f"[{self.env.now:6.2f}] {nombre} inicia CONSULTA (esperó {espera_cons:.2f} min)")
            dur_cons = random.expovariate(1.0 / self.cfg.TIEMPO_CONSULTA_PROMEDIO)
            yield self.env.timeout(dur_cons)
            if self.cfg.TRACE:
                print(f"[{self.env.now:6.2f}] {nombre} termina CONSULTA (duró {dur_cons:.2f} min)")

        total = self.env.now - llegada
        self.tiempos_totales.append(total)
        self.pacientes_completados += 1
        if self.cfg.TRACE:
            print(f"[{self.env.now:6.2f}] {nombre} sale. Total en clínica: {total:.2f} min")

    def generador_pacientes(self) -> Generator[Any, Any, None]:
        i = 0
        while True:
            inter_arribo = random.expovariate(1.0 / self.cfg.TASA_LLEGADA_PACIENTES)
            yield self.env.timeout(inter_arribo)
            i += 1
            self.env.process(self.paciente(f"Paciente {i}"))

    def run(self):
        self.env.process(self.generador_pacientes())
        self.env.run(until=self.cfg.TIEMPO_SIMULACION)
        return {
            "pacientes_completados": self.pacientes_completados,
            "prom_total_en_clinica": statistics.mean(self.tiempos_totales) if self.tiempos_totales else float("nan"),
            "max_total_en_clinica": max(self.tiempos_totales) if self.tiempos_totales else float("nan"),
            "prom_espera_registro": statistics.mean(self.tiempos_espera_registro) if self.tiempos_espera_registro else float("nan"),
            "prom_espera_consulta": statistics.mean(self.tiempos_espera_consulta) if self.tiempos_espera_consulta else float("nan"),
        }

def ejecutar_escenario(cfg: Config, etiqueta: str):
    sim = ClinicaDES(cfg)
    resumen = sim.run()
    fila = {
        "escenario": etiqueta,
        "recepcionistas": cfg.NUM_RECEPCIONISTAS,
        "medicos": cfg.NUM_MEDICOS,
        "pacientes": resumen["pacientes_completados"],
        "prom_total_min": resumen["prom_total_en_clinica"],
        "max_total_min": resumen["max_total_en_clinica"],
        "prom_esp_reg_min": resumen["prom_espera_registro"],
        "prom_esp_cons_min": resumen["prom_espera_consulta"],
    }
    return fila

if __name__ == "__main__":
    # Escenario 1 – Línea base
    base = ejecutar_escenario(Config(NUM_RECEPCIONISTAS=1, NUM_MEDICOS=2, TRACE=True), "Base (1R,2M)")
    print("\nESCENARIO 1 – LÍNEA BASE:", base)

    # Escenario 2 – Más médicos
    mas_med = ejecutar_escenario(Config(NUM_RECEPCIONISTAS=1, NUM_MEDICOS=5, TRACE=True), "Más Médicos (1R,5M)")
    print("ESCENARIO 2 – MÁS MÉDICOS:", mas_med)

    # Escenario 3 – Más recepcionistas
    mas_rec = ejecutar_escenario(Config(NUM_RECEPCIONISTAS=2, NUM_MEDICOS=2, TRACE=True), "Más Recepcionistas (2R,2M)")
    print("ESCENARIO 3 – MÁS RECEPCIONISTAS:", mas_rec)

    # Si quieren ver pasito a pasito, pueden activar TRACE=True para ver la traza de eventos