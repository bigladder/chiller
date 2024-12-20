import CoolProp.CoolProp as CP
import psychrolib

from koozie import fr_u, to_u

psychrolib.SetUnitSystem(psychrolib.SI)


class FluidState:
    def __init__(
        self,
        temperature: float,
        pressure: float = fr_u(1.0, "atm"),
        volumetric_flow_rate=None,
        mass_flow_rate=None,
    ):
        self.T = temperature
        self.p = pressure
        self._rho = -999.0
        self._cp = -999.0
        self._V_dot = -999.0
        self._m_dot = -999.0
        self.rho_set = False
        self.cp_set = False
        self._flow_rate_set = False
        self.c = 0.0
        if mass_flow_rate is not None and volumetric_flow_rate is not None:
            raise RuntimeError(
                f"Cannot set both 'volumetric_flow_rate' and 'mass_flow_rate'."
            )
        if volumetric_flow_rate is not None:
            self.V_dot = volumetric_flow_rate
            return
        if mass_flow_rate is not None:
            self.m_dot = mass_flow_rate
            return

    @property
    def m_dot(self):
        if self._flow_rate_set:
            return self._m_dot
        raise RuntimeError("m_dot not set")

    @m_dot.setter
    def m_dot(self, mass_flow_rate):
        self._m_dot = mass_flow_rate
        self._flow_rate_set = True
        self._V_dot = self.m_dot / self.rho
        self.c = self.m_dot * self.cp

    @property
    def V_dot(self):
        if self._flow_rate_set:
            return self._V_dot
        raise RuntimeError("V_dot not set")

    @V_dot.setter
    def V_dot(self, volumetric_flow_rate):
        self.m_dot = volumetric_flow_rate * self.rho

    @property
    def rho(self):
        raise NotImplementedError()

    @rho.setter
    def rho(self, rho):
        self._rho = rho
        self.rho_set = True

    @property
    def cp(self):
        raise NotImplementedError()

    @cp.setter
    def cp(self, cp):
        self._cp = cp
        self.cp_set = True

    def get_heat(self, other_state: type["FluidState"]):
        '''returns the amount of heat difference between this state and "other state"'''
        return self.c * self.T - other_state.c * other_state.T


class LiquidState(FluidState):
    def __init__(
        self,
        temperature,
        pressure=fr_u(1.0, "atm"),
        volumetric_flow_rate=None,
        mass_flow_rate=None,
        fluid_name="Water",
    ):
        self.fluid_name = fluid_name
        super().__init__(
            temperature,
            pressure,
            volumetric_flow_rate,
            mass_flow_rate,
        )

    @property
    def rho(self):
        if not self.rho_set:
            self.rho = CP.PropsSI("D", "P", self.p, "T", self.T, self.fluid_name)
        return self._rho

    @rho.setter
    def rho(self, rho):
        self._rho = rho
        self.rho_set = True

    @property
    def cp(self):
        if not self.cp_set:
            self.cp = CP.PropsSI("C", "P", self.p, "T", self.T, self.fluid_name)
        return self._cp

    @cp.setter
    def cp(self, cp):
        self._cp = cp
        self.cp_set = True

    def add_heat(self, heat):
        return LiquidState(
            temperature=self.T + heat / self.c, mass_flow_rate=self.m_dot
        )


class PsychrometricState(FluidState):
    def __init__(
        self,
        drybulb,
        pressure=fr_u(1.0, "atm"),
        volumetric_flow_rate=None,
        mass_flow_rate=None,
        **kwargs,
    ):
        super().__init__(
            drybulb,
            pressure,
            volumetric_flow_rate,
            mass_flow_rate,
        )
        self.db_C = to_u(self.T, "°C")
        self._wb = -999.0
        self._h = -999.0
        self._rh = -999.0
        self._hr = -999.0
        self.wb_set = False
        self.rh_set = False
        self.hr_set = False
        self.dp_set = False
        self.h_set = False
        self.rho_set = False
        if len(kwargs) > 1:
            raise RuntimeError(
                f"{PsychrometricState.__name__} can only be initialized with a single key word argument, but received {len(kwargs)}: {kwargs}"
            )
        if "wetbulb" in kwargs:
            self.wb = kwargs["wetbulb"]
        elif "humidity_ratio" in kwargs:
            self.hr = kwargs["humidity_ratio"]
        elif "relative_humidity" in kwargs:
            self.rh = kwargs["relative_humidity"]
        elif "enthalpy" in kwargs:
            self.h = kwargs["enthalpy"]
        else:
            raise RuntimeError(
                f"{PsychrometricState.__name__}: Unknown or missing key word argument {kwargs}."
            )

    @property
    def cp(self):
        if not self.cp_set:
            self.cp = fr_u(1.006, "kJ/kg/K")
        return self._cp

    @cp.setter
    def cp(self, cp):
        self._cp = cp
        self.cp_set = True

    @property
    def wb(self):
        if self.wb_set:
            return self._wb
        raise RuntimeError("Wetbulb not set")

    @wb.setter
    def wb(self, wb):
        self._wb = wb
        self.wb_C = to_u(self._wb, "°C")
        self.wb_set = True

    def get_wb_C(self):
        if self.wb_set:
            return self.wb_C
        else:
            raise RuntimeError("Wetbulb not set")

    @property
    def hr(self):
        if not self.hr_set:
            self.hr = psychrolib.GetHumRatioFromTWetBulb(
                self.db_C, self.get_wb_C(), self.p
            )
        return self._hr

    @hr.setter
    def hr(self, hr):
        self._hr = hr
        if not self.wb_set:
            self.wb = fr_u(
                psychrolib.GetTWetBulbFromHumRatio(self.db_C, self._hr, self.p),
                "°C",
            )

        self.hr_set = True

    @property
    def rh(self):
        if not self.rh_set:
            self.rh = psychrolib.GetHumRatioFromTWetBulb(
                self.db_C, self.get_wb_C(), self.p
            )
        return self._rh

    @rh.setter
    def rh(self, rh):
        self._rh = rh
        if not self.wb_set:
            self.wb = fr_u(
                psychrolib.GetTWetBulbFromRelHum(self.db_C, self._rh, self.p), "°C"
            )
        self.rh_set = True

    @property
    def h(self):
        if not self.h_set:
            self.h = psychrolib.GetMoistAirEnthalpy(self.db_C, self.hr)
        return self._h

    @h.setter
    def h(self, h):
        self._h = h
        if not self.hr_set:
            self.hr = psychrolib.GetHumRatioFromEnthalpyAndTDryBulb(self._h, self.db_C)
        self.h_set = True

    @property
    def rho(self):
        if not self.rho_set:
            self.rho = psychrolib.GetMoistAirDensity(self.db_C, self.hr, self.p)
        return self._rho

    @rho.setter
    def rho(self, rho):
        self._rho = rho
        self.rho_set = True


STANDARD_CONDITIONS = PsychrometricState(drybulb=fr_u(70.0, "°F"), humidity_ratio=0.0)
