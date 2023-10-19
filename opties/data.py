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
This file contains the functions to import the corresponding data and build 
a PyPSA network container.
"""

from pypsa.linopt import get_var, linexpr, define_constraints

__copyright__ = (
    "Europa-Universität Flensburg, Centre for Sustainable Energy Systems, "
    "FossilExit Research Group"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "KathiEsterl"

import pandas as pd
import geopandas as gpd
import shapely
import pypsa


def import_data(path="data/"):
    # Import von Komponenten aus csv-Dateien

    buses = pd.read_csv(path + "buses.csv").set_index("name")
    buses["geometry"] = buses["geometry"].apply(shapely.wkt.loads)
    buses = gpd.GeoDataFrame(buses, geometry="geometry")

    lines = pd.read_csv(path + "lines.csv").set_index("id")
    generators = pd.read_csv(path + "generators.csv").set_index("name")
    storage_units = pd.read_csv(path + "storage_units.csv").set_index("name")
    stores = pd.read_csv(path + "stores.csv").set_index("name")
    links = pd.read_csv(path + "links.csv").set_index("name")
    loads = pd.read_csv(path + "loads.csv").set_index("name")

    loads = loads.drop(["LS1", "LS2"])  # TODO: noch ohne E-Mob

    return buses, lines, generators, storage_units, stores, links, loads


def import_timeseries(path="data/timeseries/"):
    el_loads = pd.read_csv(path + "el_load_synth.csv").set_index("time")
    el_loads.index = pd.date_range("2019-01-01 00:00", "2019-12-31 23:00", freq="H")

    heat_load = pd.read_csv(path + "heat_load_synth.csv").set_index("time")
    heat_load.index = pd.date_range("2019-01-01 00:00", "2019-12-31 23:00", freq="H")

    pv = pd.read_csv(path + "pv_timeseries.csv")
    pv = pd.Series(
        pv["p_max_pu"].values,
        index=pd.date_range("2019-01-01 00:00", "2019-12-31 23:00", freq="H"),
    )

    return el_loads, heat_load, pv


def create_pypsa_network(
    buses,
    lines,
    generators,
    storage_units,
    stores,
    links,
    loads,
    el_loads,
    heat_load,
    pv,
):
    network = pypsa.Network()

    network.set_snapshots(
        pd.date_range("2019-01-01 00:00", "2019-12-31 23:00", freq="H")
    )

    # Buses

    for i in range(0, len(buses)):
        bus = buses.iloc[i]
        network.add(
            "Bus",
            name=bus.name,
            carrier=bus.carrier,
            v_nom=bus.v_nom,
            x=shapely.get_x(bus.geometry),
            y=shapely.get_y(bus.geometry),
        )

    # Lines

    for i in range(0, len(lines)):
        line = lines.iloc[i]
        network.add(
            "Line",
            name=line.name,
            type=line.type,
            bus0=line.bus0,
            bus1=line.bus1,
            s_nom_extendable=line.s_nom_extendable,
            s_nom_min=line.s_nom_min,
            s_nom=line.s_nom,
            length=line.length,
            capital_cost=line.capital_cost,
        )

    # Generation

    for i in range(0, len(generators)):
        gen = generators.iloc[i]
        if gen.carrier == "PV":
            network.add(
                "Generator",
                name=gen.name,
                carrier=gen.carrier,
                bus=gen.bus,
                control=gen.control,
                p_nom=gen.p_nom,
                p_nom_extendable=gen.p_nom_extendable,
                marginal_cost=gen.marginal_cost,
                capital_cost=gen.capital_cost,
                p_max_pu=pv,
            )
        else:
            network.add(
                "Generator",
                name=gen.name,
                carrier=gen.carrier,
                bus=gen.bus,
                control=gen.control,
                p_nom=gen.p_nom,
                p_nom_extendable=gen.p_nom_extendable,
                marginal_cost=gen.marginal_cost,
                capital_cost=gen.capital_cost,
            )

    # Storage Units

    for i in range(0, len(storage_units)):
        sto = storage_units.iloc[i]
        network.add(
            "StorageUnit",
            name=sto.name,
            carrier=sto.carrier,
            bus=sto.bus,
            p_nom_extendable=sto.p_nom_extendable,
            p_nom=sto.p_nom,
            p_nom_min=sto.p_nom_min,
            max_hours=sto.max_hours,
            standing_loss=sto.standing_loss,
            efficiency_store=sto.efficiency_store,
            efficiency_dispatch=sto.efficiency_dispatch,
            cyclic_state_of_charge=sto.cyclic_state_of_charge,
            marginal_cost=sto.marginal_cost,
            capital_cost=sto.capital_cost,
        )

    # Stores

    for i in range(0, len(stores)):
        sto = stores.iloc[i]
        network.add(
            "Store",
            name=sto.name,
            carrier=sto.carrier,
            bus=sto.bus,
            e_nom_extendable=sto.e_nom_extendable,
            e_nom=sto.e_nom,
            e_nom_min=sto.e_nom_min,
            standing_loss=sto.standing_loss,
            e_cyclic=sto.e_cyclic,
            marginal_cost=sto.marginal_cost,
            capital_cost=sto.capital_cost,
        )

    # Links

    for i in range(0, len(links)):
        link = links.iloc[i]
        network.add(
            "Link",
            name=link.name,
            carrier=link.carrier,
            bus0=link.bus0,
            bus1=link.bus1,
            p_nom_extendable=link.p_nom_extendable,
            p_nom=link.p_nom,
            efficiency=link.efficiency,
            marginal_cost=link.marginal_cost,
            capital_cost=link.capital_cost,
        )

    # Loads

    for i in range(0, len(loads)):
        load = loads.iloc[i]
        if load.carrier == "AC":
            network.add(
                "Load",
                name=load.name,
                carrier=load.carrier,
                bus=load.bus,
                p_set=el_loads[load.bus],
            )
        else:
            network.add(
                "Load",
                name=load.name,
                carrier=load.carrier,
                bus=load.bus,
                p_set=heat_load["aggregierte Erzeugung"],
            )

    return network
