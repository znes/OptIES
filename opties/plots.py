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


def AC_load(network, snapshots=[0,8759]):
    ac = network.loads[network.loads.carrier == "AC"]

    network.loads_t.p[ac.index].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot()


def AN_load(network, snapshots=[0,8759]):
    ac = network.loads[network.loads.carrier == "AC"]
    ac.drop('EV_el', inplace=True)
    
    network.loads_t.p[ac.index].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot()


def heat_load(network, snapshots=[0,8759]):
    heat = network.loads[network.loads.carrier == "heat"].index

    network.loads_t.p[heat].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot()

    network.links_t.p0["TA"].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label="TA", legend=True)


# elektrische Einspeisung


def el_gen(network, snapshots=[0,8759]):
    AC_gen = network.generators[
        network.generators.bus.isin(network.buses[network.buses.carrier == "AC"].index)
    ].index

    network.generators_t.p[AC_gen].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot()


# Wärmeerzeugung


def heat_gen(network, snapshots=[0,8759]):
    network.generators_t.p["SpK"].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label="SpK", legend=True)

    abs(network.links_t.p1["KWK1_W"]).iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label="KWK1_W", legend=True)

    abs(network.links_t.p1["KWK2_W"]).iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label="KWK2_W", legend=True)

    abs(network.links_t.p1["KWK3_W"]).iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label="KWK3_W", legend=True)


# Nutzung der PV-Anlagen


def pv_gen(network, snapshots=[0,8759]):
    pv = network.generators[network.generators.carrier=='PV']
    
    network.generators_t.p[pv.index].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot()


# Nutzung des Batteriespeichers


def battery_usage(network, snapshots=[0,8759]):
    network.storage_units_t.state_of_charge.iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot()


def battery_pv_usage(network, snapshots=[0,8759]):
    pv = network.generators[network.generators.carrier=='PV']
    
    network.generators_t.p[pv.index[0]].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label='PV1', legend=True)
    network.generators_t.p[pv.index[1]].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label='PV2', legend=True)
    
    abs(network.storage_units_t.p[network.storage_units_t.p<0].fillna(0)).iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label='BSp', legend=True)


# Nutzung des Wärmespeichers

def heat_store_usage(network, snapshots=[0,8759]):
    network.stores_t.e["WSp"].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot()


def heat_gen_store_usage(network, snapshots=[0,8759]):
    network.generators_t.p["SpK"].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label="SpK", legend=True)

    abs(network.links_t.p1["KWK1_W"]).iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label="KWK1_W", legend=True)
    abs(network.links_t.p1["KWK2_W"]).iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label="KWK2_W", legend=True)
    abs(network.links_t.p1["KWK3_W"]).iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label="KWK3_W", legend=True)
    
    network.links_t.p0["W_entladen"].iloc[snapshots[0]:snapshots[1]].resample("5H").mean().plot(label="WSp", legend=True)


# KWKs und BGA


def gas_gen_store(network):
    gas = pd.DataFrame(
        columns=[
            "BGA1 - Erzeugung",
            "BGA1 - Speicher",
            "BGA2 - Erzeugung",
            "BGA2 - Speicher",
        ],
        index=network.generators_t.p.index[0::5],
    )

    gas["BGA1 - Erzeugung"] = network.generators_t.p["BGA1"].resample("5H").mean()

    gas["BGA2 - Erzeugung"] = network.generators_t.p["BGA2"].resample("5H").mean()

    gas["BGA1 - Speicher"] = network.stores_t.e["GSp1"].resample("5H").mean()

    gas["BGA2 - Speicher"] = network.stores_t.e["GSp2"].resample("5H").mean()

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
        index=network.links_t.p0.index[0::5],
    )

    gas["Anlage 1: KWK1"] = network.links_t.p0["KWK1_AC"] + network.links_t.p0["KWK1_W"].resample("5H").mean()

    gas["Anlage 1: KWK2"] = network.links_t.p0["KWK2_AC"] + network.links_t.p0["KWK2_W"].resample("5H").mean()

    gas["Anlage 2: KWK3"] = network.links_t.p0["KWK3_AC"] + network.links_t.p0["KWK3_W"].resample("5H").mean()

    gas["Anlage 2: Sat-KWK"] = network.loads_t.p["SAT"].resample("5H").mean()

    gas["Gasverfügbarkeit Anlage 1"] = (
        network.generators_t.p["BGA1"] + network.stores_t.e["GSp1"]
    ).resample("5H").mean()

    gas["Gasverfügbarkeit Anlage 2"] = (
        network.generators_t.p["BGA2"] + network.stores_t.e["GSp2"]
    ).resample("5H").mean()

    gas.plot()


def kwk_gas_usage(network):
    gas = pd.DataFrame(columns=["KWK1", "KWK2", "KWK3"], index=network.links_t.p0.index[0::5])

    gas["KWK1"] = network.links_t.p0["KWK1_AC"] + network.links_t.p0["KWK1_W"].resample("5H").mean()

    gas["KWK2"] = network.links_t.p0["KWK2_AC"] + network.links_t.p0["KWK2_W"].resample("5H").mean()

    gas["KWK3"] = network.links_t.p0["KWK3_AC"] + network.links_t.p0["KWK3_W"].resample("5H").mean()

    gas.plot()


def kwk_electrical_output(network):
    gas = pd.DataFrame(columns=["KWK1", "KWK2", "KWK3"], index=network.links_t.p0.index[0::5])

    gas["KWK1"] = abs(network.links_t.p1["KWK1_AC"]).resample("5H").mean()

    gas["KWK2"] = abs(network.links_t.p1["KWK2_AC"]).resample("5H").mean()

    gas["KWK3"] = abs(network.links_t.p1["KWK3_AC"]).resample("5H").mean()

    gas.plot()


def kwk_heat_output(network):
    gas = pd.DataFrame(columns=["KWK1", "KWK2", "KWK3"], index=network.links_t.p0.index[0::5])

    gas["KWK1"] = abs(network.links_t.p1["KWK1_W"]).resample("5H").mean()

    gas["KWK2"] = abs(network.links_t.p1["KWK2_W"]).resample("5H").mean()

    gas["KWK3"] = abs(network.links_t.p1["KWK3_W"]).resample("5H").mean()

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
        index=network.links_t.p0.index[0::5],
    )

    # abs(network.links_t.p1[network.links[network.links.index.str.startswith("KWK1")].index]).plot()

    gas["KWK1-Strom"] = abs(network.links_t.p1["KWK1_AC"]).resample("5H").mean()

    gas["KWK2-Strom"] = abs(network.links_t.p1["KWK2_AC"]).resample("5H").mean()

    gas["KWK3-Strom"] = abs(network.links_t.p1["KWK3_AC"]).resample("5H").mean()

    gas["KWK1-Wärme"] = abs(network.links_t.p1["KWK1_W"]).resample("5H").mean()

    gas["KWK2-Wärme"] = abs(network.links_t.p1["KWK2_W"]).resample("5H").mean()

    gas["KWK3-Wärme"] = abs(network.links_t.p1["KWK3_W"]).resample("5H").mean()

    gas.plot()
