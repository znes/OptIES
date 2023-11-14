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
import matplotlib.pyplot as plt

__copyright__ = (
    "Europa-Universität Flensburg, Centre for Sustainable Energy Systems, "
    "FossilExit Research Group"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "KathiEsterl"


# Netz


def plot_network(network):
    network.plot(bus_sizes=0.00000001, line_widths=1, link_widths=1)
    # TODO (optional): map in Hintergrund


# Lasten


def AC_load(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("elektrische Last in kW")
    ax.set_xlabel("Zeitschritte")

    ac = network.loads[network.loads.carrier == "AC"]
    ax.plot(
        (
            network.loads_t.p[ac.index]
            .iloc[snapshots[0] : snapshots[1]]
            .resample("5H")
            .mean()
        )
        * 1000,
        label=ac.index,
    )

    fig.legend(loc="upper right")


def AN_load(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("elektrische Last in kW")
    ax.set_xlabel("Zeitschritte")

    ac = network.loads[network.loads.carrier == "AC"]
    ac.drop("EV_el", inplace=True)
    ax.plot(
        (
            network.loads_t.p[ac.index]
            .iloc[snapshots[0] : snapshots[1]]
            .resample("5H")
            .mean()
        )
        * 1000,
        label=ac.index,
    )

    fig.legend(loc="upper right")


def heat_load(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("elektrische Last in MW")
    ax.set_xlabel("Zeitschritte")

    heat = network.loads[network.loads.carrier == "heat"].index
    for index in heat:
        ax.plot(
            network.loads_t.p[index]
            .iloc[snapshots[0] : snapshots[1]]
            .resample("5H")
            .mean(),
            label=index,
        )
    ax.plot(
        network.links_t.p0["TA"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="TA",
    )

    fig.legend(loc="upper right")


# Netzeinspeiung und Netzbezug


def grid_usage(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("Leistung in kW")
    ax.set_xlabel("Zeitschritte")

    ax.plot(
        network.generators_t.p["NeAn"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="Netzbezug",
    )
    ax.plot(
        network.links_t.p0["NA_Sp"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="Einspeisung ins Netz",
    )

    fig.legend(loc="upper right")


# elektrische Einspeisung in das IES


def el_gen_ies(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("elektrische Versorgung des IES in kW")
    ax.set_xlabel("Zeitschritte")

    ax.plot((network.links_t.p0["IES"].resample("5H").mean() * 1000), label="BGA")
    pv = network.generators[network.generators.carrier == "PV"]
    ax.plot(
        (
            network.generators_t.p[pv.index]
            .iloc[snapshots[0] : snapshots[1]]
            .resample("5H")
            .mean()
        )
        * 1000,
        label=pv.index,
    )

    fig.legend(loc="upper right")


# Nutzung der PV-Anlagen


def pv_gen(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("elektrische Einspeisung in kW")
    ax.set_xlabel("Zeitschritte")

    pv = network.generators[network.generators.carrier == "PV"]
    ax.plot(
        (
            network.generators_t.p[pv.index]
            .iloc[snapshots[0] : snapshots[1]]
            .resample("5H")
            .mean()
        )
        * 1000,
        label=pv.index,
    )

    fig.legend(loc="upper right")


# Nutzung des Batteriespeichers


def battery_usage(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("Ladezustand der Batterie in kWh")
    ax.set_xlabel("Zeitschritte")

    ax.plot(
        (
            network.storage_units_t.state_of_charge.iloc[snapshots[0] : snapshots[1]]
            .resample("5H")
            .mean()
        )
        * 1000,
        label="BSp",
    )

    fig.legend(loc="upper right")


def battery_pv_usage(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("elektrische Einspeisung in kW")
    ax.set_xlabel("Zeitschritte")

    pv = network.generators[network.generators.carrier == "PV"]
    ax.plot(
        (
            network.generators_t.p[pv.index]
            .iloc[snapshots[0] : snapshots[1]]
            .resample("5H")
            .mean()
        )
        * 1000,
        label=pv.index,
    )
    ax.plot(
        abs(
            (network.storage_units_t.p[network.storage_units_t.p < 0].fillna(0))
            .iloc[snapshots[0] : snapshots[1]]
            .resample("5H")
            .mean()
            * 1000
        ),
        label="BSp",
    )

    fig.legend(loc="upper right")


# Wärmeerzeugung


def heat_gen(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("Wärmeerzeugung in MW")
    ax.set_xlabel("Zeitschritte")

    ax.plot(
        network.generators_t.p["SpK"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="SpK",
    )
    ax.plot(
        abs(network.links_t.p1["KWK1_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="KWK1_W",
    )
    ax.plot(
        abs(network.links_t.p1["KWK2_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="KWK2_W",
    )
    ax.plot(
        abs(network.links_t.p1["KWK3_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="KWK3_W",
    )

    fig.legend(loc="upper right")


# Nutzung des Wärmespeichers


def heat_store_usage(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("Ladezustand des Wärmespeichers in MWh")
    ax.set_xlabel("Zeitschritte")

    ax.plot(
        network.stores_t.e["WSp"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="WSp",
    )

    fig.legend(loc="upper right")


def heat_gen_store_usage(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("Wärmeeinspeisung in MW")
    ax.set_xlabel("Zeitschritte")

    ax.plot(
        network.generators_t.p["SpK"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="SpK",
    )
    ax.plot(
        abs(network.links_t.p1["KWK1_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="KWK1_W",
    )
    ax.plot(
        abs(network.links_t.p1["KWK2_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="KWK2_W",
    )
    ax.plot(
        abs(network.links_t.p1["KWK3_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="KWK3_W",
    )
    ax.plot(
        network.links_t.p0["W_entladen"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="WSp",
    )

    fig.legend(loc="upper right")


# KWKs und BGA


def gas_gen_store(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("Gasverfügbarkeit")
    ax.set_xlabel("Zeitschritte")

    ax.plot(
        network.generators_t.p["BGA1"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="BGA1 - Erzeugung in MW",
    )
    ax.plot(
        network.generators_t.p["BGA2"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="BGA2 - Erzeugung in MW",
    )
    ax.plot(
        network.stores_t.e["GSp1"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="BGA1 - Speicherfüllstand in MWh",
    )
    ax.plot(
        network.stores_t.e["GSp2"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="BGA2 - Speicherfüllstand in MWh",
    )

    fig.legend(loc="upper right")


def gas_gen_usage(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("Gasverfügbarkeit und Gasnutzung")
    ax.set_xlabel("Zeitschritte")

    ax.plot(
        (
            network.links_t.p0["KWK1_AC"].iloc[snapshots[0] : snapshots[1]]
            + network.links_t.p0["KWK1_W"].iloc[snapshots[0] : snapshots[1]]
        )
        .resample("5H")
        .mean(),
        label="KWK1 - Gasnutzung in MW",
    )
    ax.plot(
        (
            network.links_t.p0["KWK2_AC"].iloc[snapshots[0] : snapshots[1]]
            + network.links_t.p0["KWK3_W"].iloc[snapshots[0] : snapshots[1]]
        )
        .resample("5H")
        .mean(),
        label="KWK2 - Gasnutzung in MW",
    )
    ax.plot(
        (
            network.links_t.p0["KWK3_AC"].iloc[snapshots[0] : snapshots[1]]
            + network.links_t.p0["KWK2_W"].iloc[snapshots[0] : snapshots[1]]
        )
        .resample("5H")
        .mean(),
        label="KWK3 - Gasnutzung in MW",
    )
    ax.plot(
        network.loads_t.p["SAT"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="SAT-KWK - Gasnutzung in MW",
    )
    ax.plot(
        (
            network.generators_t.p["BGA1"].iloc[snapshots[0] : snapshots[1]]
            + network.stores_t.e["GSp1"].iloc[snapshots[0] : snapshots[1]]
        )
        .resample("5H")
        .mean(),
        label="Anlage 1 - Gasverfügbarkeit in MWh",
    )
    ax.plot(
        (
            network.generators_t.p["BGA2"].iloc[snapshots[0] : snapshots[1]]
            + network.stores_t.e["GSp2"].iloc[snapshots[0] : snapshots[1]]
        )
        .resample("5H")
        .mean(),
        label="Anlage 2 - Gasverfügbarkeit in MWh",
    )

    fig.legend(loc="upper right")


def kwk_gas_usage(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("Gasnutzung in MW")
    ax.set_xlabel("Zeitschritte")

    ax.plot(
        (
            network.links_t.p0["KWK1_AC"].iloc[snapshots[0] : snapshots[1]]
            + network.links_t.p0["KWK1_W"].iloc[snapshots[0] : snapshots[1]]
        )
        .resample("5H")
        .mean(),
        label="KWK1",
    )
    ax.plot(
        (
            network.links_t.p0["KWK2_AC"].iloc[snapshots[0] : snapshots[1]]
            + network.links_t.p0["KWK3_W"].iloc[snapshots[0] : snapshots[1]]
        )
        .resample("5H")
        .mean(),
        label="KWK2",
    )
    ax.plot(
        (
            network.links_t.p0["KWK3_AC"].iloc[snapshots[0] : snapshots[1]]
            + network.links_t.p0["KWK2_W"].iloc[snapshots[0] : snapshots[1]]
        )
        .resample("5H")
        .mean(),
        label="KWK3",
    )
    ax.plot(
        network.loads_t.p["SAT"]
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean(),
        label="SAT-KWK",
    )

    fig.legend(loc="upper right")


def kwk_electrical_output(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("Stromerzeugung in kW")
    ax.set_xlabel("Zeitschritte")

    ax.plot(
        abs(network.links_t.p1["KWK1_AC"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK1",
    )
    ax.plot(
        abs(network.links_t.p1["KWK2_AC"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK2",
    )
    ax.plot(
        abs(network.links_t.p1["KWK3_AC"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK3",
    )

    fig.legend(loc="upper right")


def kwk_heat_output(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("Wärmeerzeugung in kW")
    ax.set_xlabel("Zeitschritte")

    ax.plot(
        abs(network.links_t.p1["KWK1_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK1",
    )
    ax.plot(
        abs(network.links_t.p1["KWK2_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK2",
    )
    ax.plot(
        abs(network.links_t.p1["KWK3_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK3",
    )

    fig.legend(loc="upper right")


def kwk_output(network, snapshots=[0, 8759]):
    fig, ax = plt.subplots()
    ax.set_ylabel("Strom- und Wärmeerzeugung in kW")
    ax.set_xlabel("Zeitschritte")

    ax.plot(
        abs(network.links_t.p1["KWK1_AC"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK1 - Strom",
    )
    ax.plot(
        abs(network.links_t.p1["KWK2_AC"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK2 - Strom",
    )
    ax.plot(
        abs(network.links_t.p1["KWK3_AC"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK3 - Strom",
    )
    ax.plot(
        abs(network.links_t.p1["KWK1_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK1 - Wärme",
    )
    ax.plot(
        abs(network.links_t.p1["KWK2_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK2 - Wärme",
    )
    ax.plot(
        abs(network.links_t.p1["KWK3_W"])
        .iloc[snapshots[0] : snapshots[1]]
        .resample("5H")
        .mean()
        * 1000,
        label="KWK3 - Wärme",
    )

    fig.legend(loc="upper right")
