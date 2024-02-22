from re import S
import CoolProp.CoolProp as CP
from koozie import fr_u


class FluidState:
    def __init__(
        self,
        temperature,
        pressure=fr_u(1.0, "atm"),
        volumetric_flow_rate=None,
        mass_flow_rate=None,
        fluid_name="Water",
    ):
        self.fluid_name = fluid_name
        self.T = temperature
        self.p = pressure
        self.rho_set = False
        self.cp_set = False
        self.V_dot_set = False
        if mass_flow_rate is not None and volumetric_flow_rate is not None:
            raise Exception(
                f"Cannot set both 'volumetric_flow_rate' and 'mass_flow_rate'."
            )
        if volumetric_flow_rate is None:
            self.V_dot = None
        else:
            self.set_V_dot(volumetric_flow_rate)
            return
        if mass_flow_rate is None:
            self.m_dot = None
        else:
            self.set_m_dot(mass_flow_rate)
            return

    def get_rho(self):
        if not self.rho_set:
            self.rho = CP.PropsSI("D", "P", self.p, "T", self.T, self.fluid_name)
            self.rho_set = True
        return self.rho

    def get_cp(self):
        if not self.cp_set:
            self.cp = CP.PropsSI("C", "P", self.p, "T", self.T, self.fluid_name)
            self.cp_set = True
        return self.cp

    def set_V_dot(self, volumetric_flow_rate):
        self.V_dot = volumetric_flow_rate
        self.m_dot = self.V_dot * self.get_rho()
        self.c = self.m_dot * self.get_cp()
        self.V_dot_set = True

    def set_m_dot(self, mass_flow_rate):
        self.m_dot = mass_flow_rate
        self.V_dot = self.m_dot / self.get_rho()
        self.c = self.m_dot * self.get_cp()
        self.V_dot_set = True

    def add_heat(self, heat):
        return FluidState(temperature=self.T + heat / self.c, mass_flow_rate=self.m_dot)

    def get_heat(self, other_state):
        '''returns the amount of heat difference between this state and "other state"'''
        return self.c * self.T - other_state.c * other_state.T
