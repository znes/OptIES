# -*- coding: utf-8 -*-
# Copyright 2023
# Europa-Universität Flensburg,
# Centre for Sustainable Energy Systems,
# FossilExit Research Group

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# File description
"""
This file contains the functions related to plot the optimization results.
"""

import pandas as pd

__copyright__ = (
    "Europa-Universität Flensburg, Centre for Sustainable Energy Systems, "
    "FossilExit Research Group"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "KathiEsterl"


# Netz


def plot_network(network):
    network.plot(bus_sizes=0.00000001, line_widths=1, link_widths=1)


# Lasten


def AC_load(network):
    ac = network.loads[network.loads.carrier == "AC"]

    network.loads_t.p[ac].plot()

    # TODO:
    # network.loads_t.p.iloc[:, :7].plot()
    # network.loads_t.p.iloc[:, :7][0:336].plot()


def heat_load(network):
    heat = network.loads[network.loads.carrier == "heat"].index

    network.loads_t.p[heat].plot()

    network.links_t.p0["TA"].plot()

    # TODO:
    # network.loads_t.p.iloc[:, :7].plot()
    # network.loads_t.p.iloc[:, :7][0:336].plot()


# elektrische Einspeisung


def el_gen(network):
    AC_gen = network.generators[
        network.generators.bus.isin(network.buses[network.buses.carrier == "AC"].index)
    ].index

    network.generators_t.p[AC_gen].plot()


# Wärmeerzeugung


def heat_gen(network):
    network.generators_t.p["SpK"].plot()

    abs(network.links_t.p1["KWK1_W"]).plot()

    abs(network.links_t.p1["KWK2_W"]).plot()

    abs(network.links_t.p1["KWK3_W"]).plot()


# Nutzung der PV-Anlagen


def pv_gen(network):
    network.generators_t.p


# Nutzung des Batteriespeichers


def battery_usage(network):
    network.storage_units_t.state_of_charge.plot()


# Nutzung des Wärmespeichers


def heat_store_usage(network):
    network.stores_t["WSp"].e.plot()


# KWKs und BGA


def gas_gen_store(network):
    gas = pd.DataFrame(
        columns=[
            "BGA1 - Erzeugung",
            "BGA1 - Speicher",
            "BGA2 - Erzeugung",
            "BGA2 - Speicher",
        ],
        index=network.generators_t.p.index,
    )

    gas["BGA1 - Erzeugung"] = network.generators_t.p["BGA1"]

    gas["BGA2 - Erzeugung"] = network.generators_t.p["BGA2"]

    gas["BGA1 - Speicher"] = network.stores_t.e["GSp1"]

    gas["BGA2 - Speicher"] = network.stores_t.e["GSp2"]

    gas.plot()


def gas_gen_usage(network):
    gas = pd.DataFrame(
        columns=[
            "Anlage 1: KWK1",
            "Anlage 1: KWK2",
            "Anlage 2: KWK3",
            "Anlage 2: Sat-KWK",
            "Gasverfügbarkeit Anlage 1",
            "Gasverfügbarkeit Anlage 2",
        ],
        index=network.links_t.p0.index,
    )

    gas["Anlage 1: KWK1"] = network.links_t.p0["KWK1_AC"] + network.links_t.p0["KWK1_W"]

    gas["Anlage 1: KWK2"] = network.links_t.p0["KWK2_AC"] + network.links_t.p0["KWK2_W"]

    gas["Anlage 2: KWK3"] = network.links_t.p0["KWK3_AC"] + network.links_t.p0["KWK3_W"]

    gas["Anlage 2: Sat-KWK"] = network.loads_t.p["SAT"]

    gas["Gasverfügbarkeit Anlage 1"] = (
        network.generators_t.p["BGA1"] + network.stores_t.e["GSp1"]
    )

    gas["Gasverfügbarkeit Anlage 2"] = (
        network.generators_t.p["BGA2"] + network.stores_t.e["GSp2"]
    )

    gas.plot()


def kwk_gas_usage(network):
    gas = pd.DataFrame(columns=["KWK1", "KWK2", "KWK3"], index=network.links_t.p0.index)

    gas["KWK1"] = network.links_t.p0["KWK1_AC"] + network.links_t.p0["KWK1_W"]

    gas["KWK2"] = network.links_t.p0["KWK2_AC"] + network.links_t.p0["KWK2_W"]

    gas["KWK3"] = network.links_t.p0["KWK3_AC"] + network.links_t.p0["KWK3_W"]

    gas.plot()


def kwk_electrical_output(network):
    gas = pd.DataFrame(columns=["KWK1", "KWK2", "KWK3"], index=network.links_t.p0.index)

    gas["KWK1"] = abs(network.links_t.p1["KWK1_AC"])

    gas["KWK2"] = abs(network.links_t.p1["KWK2_AC"])

    gas["KWK3"] = abs(network.links_t.p1["KWK3_AC"])

    gas.plot()


def kwk_heat_output(network):
    gas = pd.DataFrame(columns=["KWK1", "KWK2", "KWK3"], index=network.links_t.p0.index)

    gas["KWK1"] = abs(network.links_t.p1["KWK1_W"])

    gas["KWK2"] = abs(network.links_t.p1["KWK2_W"])

    gas["KWK3"] = abs(network.links_t.p1["KWK3_W"])

    gas.plot()


def kwk_output(network):
    gas = pd.DataFrame(
        columns=[
            "KWK1-Strom",
            "KWK1-Wärme",
            "KWK2-Strom",
            "KWK2-Wärme",
            "KWK3-Strom",
            "KWK3-Wärme",
        ],
        index=network.links_t.p0.index,
    )

    # abs(network.links_t.p1[network.links[network.links.index.str.startswith("KWK1")].index]).plot()

    gas["KWK1-Strom"] = abs(network.links_t.p1["KWK1_AC"])

    gas["KWK2-Strom"] = abs(network.links_t.p1["KWK2_AC"])

    gas["KWK3-Strom"] = abs(network.links_t.p1["KWK3_AC"])

    gas["KWK1-Wärme"] = abs(network.links_t.p1["KWK1_W"])

    gas["KWK2-Wärme"] = abs(network.links_t.p1["KWK2_W"])

    gas["KWK3-Wärme"] = abs(network.links_t.p1["KWK3_W"])

    gas.plot()
