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

# TODO: in Funktionn gießen
# TODO: ergänzen

# plot network

network.plot(bus_sizes=0.00000001, line_widths=1, link_widths=1)

# plot AC loads

network.loads_t.p.iloc[:, :7].plot()
network.loads_t.p.iloc[:, :7][0:336].plot()

# plot heat load

network.loads_t.p["WL"].iloc[0:336].plot()
network.loads_t.p["WL"].iloc[0:336].plot()

# plot potential generation

network.generators_t.p_max_pu.plot()

# plot generation

network.generators_t.p.plot()

AC_gen = network.generators[
    network.generators.bus.isin(network.buses[network.buses.carrier == "AC"].index)
].index

network.generators_t.p[AC_gen].plot()

network.generators_t.p[AC_gen].iloc[0:336].plot()

# plot CHPs

abs(
    network.links_t.p1[network.links[network.links.index.str.startswith("KWK1")].index]
).plot()

# plot AC links

AC_links = network.links[
    network.links.bus1.isin(network.buses[network.buses.carrier == "AC"].index)
].index

network.links_t.p0[AC_links].plot()


# plot battery storage

network.storage_units_t.state_of_charge.plot()

network.storage_units_t.state_of_charge.iloc[0:336].plot()

# KWKs und BGA


def kwk_gas_usage(network):
    gas = pd.DataFrame(columns=["KWK1", "KWK2", "KWK3"], index=network.links_t.p0.index)

    gas["KWK1"] = network.links_t.p0["KWK1_AC"] + network.links_t.p0["KWK1_W"]

    gas["KWK2"] = network.links_t.p0["KWK2_AC"] + network.links_t.p0["KWK2_W"]

    gas["KWK3"] = network.links_t.p0["KWK3_AC"] + network.links_t.p0["KWK3_W"]

    gas.plot()


def kwk_gas_output(network):
    gas = pd.DataFrame(columns=["KWK1", "KWK2", "KWK3"], index=network.links_t.p0.index)

    gas["KWK1"] = network.links_t.p0["KWK1_AC"] + network.links_t.p0["KWK1_W"]

    gas["KWK2"] = network.links_t.p0["KWK2_AC"] + network.links_t.p0["KWK2_W"]

    gas["KWK3"] = network.links_t.p0["KWK3_AC"] + network.links_t.p0["KWK3_W"]

    gas.plot()


def gas_gen_usage(network):
    gas = pd.DataFrame(
        columns=["KWK1", "KWK2", "KWK3", "availability_F1", "availability_F2"],
        index=network.links_t.p0.index,
    )

    gas["KWK1"] = network.links_t.p0["KWK1_AC"] + network.links_t.p0["KWK1_W"]

    gas["KWK2"] = network.links_t.p0["KWK2_AC"] + network.links_t.p0["KWK2_W"]

    gas["KWK3"] = network.links_t.p0["KWK3_AC"] + network.links_t.p0["KWK3_W"]

    gas["availability_F1"] = network.generators_t.p["BGA1"] + network.stores_t.e["GSp1"]

    gas["availability_F2"] = network.generators_t.p["BGA2"] + network.stores_t.e["GSp2"]

    gas.plot()


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
