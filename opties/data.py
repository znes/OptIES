# -*- coding: utf-8 -*-
# Copyright 2023
# Europa-Universität Flensburg,
# Centre for Sustainable Energy Systems

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

import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
import pypsa

from pypsa.linopt import get_var, linexpr, define_constraints

__copyright__ = (
    "Europa-Universität Flensburg, Centre for Sustainable Energy Systems, "
    "FossilExit Research Group"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "KathiEsterl"


def import_data(args):
    path = args["path"]

    if args["IES_extension"]["extension"]:
        path = args["path"] + "data_extension/"

    buses = pd.read_csv(path + "buses.csv").set_index("name")
    if "geometry" in buses.columns:
        buses["geometry"] = buses["geometry"].apply(shapely.wkt.loads)
        buses = gpd.GeoDataFrame(buses, geometry="geometry")

    lines = pd.read_csv(path + "lines.csv").set_index("id")
    generators = pd.read_csv(path + "generators.csv").set_index("name")
    storage_units = pd.read_csv(path + "storage_units.csv").set_index("name")
    stores = pd.read_csv(path + "stores.csv").set_index("name")
    links = pd.read_csv(path + "links.csv").set_index("name")
    loads = pd.read_csv(path + "loads.csv").set_index("name")

    if args["IES_extension"]["postEEG"]:
        generators = pd.read_csv(path + "generatorsIES2_nachEEG.csv").set_index("name")
        links = pd.read_csv(path + "links_IES2_nachEEG.csv").set_index("name")

    return buses, lines, generators, storage_units, stores, links, loads


def import_timeseries(args):
    path = args["path"]+"timeseries/"
    use_real_data = args["use_real_data"]
    temporal = args["temporal_resolution"]

    if args["IES_extension"]["extension"]:
        path = args["path"] + "data_extension/timeseries/"

    if use_real_data:
        # anpassen der network snapshots sowie der synthetischen Zeitreihen
        # entsprechend des Zeitabschnitts der Messungen (Febraur 2023 - Februar 2024)
        # und der der/des Nutzer*in gewählten zeitlichen Auflösung

        el_loads = pd.read_csv(path + "el_load_real.csv").set_index("time")
        el_loads.index = pd.date_range(
            "2023-02-14 00:00", "2024-02-13 23:55", freq="5min"
        )

        if temporal == "5min":
            res = 12
            index = pd.date_range("2023-02-14 00:00", "2024-02-13 23:55", freq="5min")
        elif temporal == "15min":
            res = 4
            index = pd.date_range("2023-02-14 00:00", "2024-02-13 23:45", freq="15min")
            eloads = el_loads.copy()
            el_loads = pd.DataFrame(index=index)
            el_loads = eloads.groupby(np.arange(len(eloads)) // 3).mean()
            el_loads = el_loads.set_index(index)
        elif temporal == "hourly":
            res = 1
            index = pd.date_range("2023-02-14 00:00", "2024-02-13 23:00", freq="1H")
            eloads = el_loads.copy()
            el_loads = pd.DataFrame(index=index)
            el_loads = eloads.groupby(np.arange(len(eloads)) // 12).mean()
            el_loads = el_loads.set_index(index)

        hload = pd.read_csv(path + "heat_load_synth.csv").set_index("time")
        hload = hload.append(hload[:1056], ignore_index=True)
        hload = hload.drop(hload.index[:1056])
        heat_load = pd.DataFrame(index=index)
        heat_load["WL"] = hload["WL"].values.repeat(res)
        heat_load["EV_W"] = hload["EV_W"].values.repeat(res)

        gload = pd.read_csv(path + "gas_load_synth.csv").set_index("time")
        gload = gload.append(gload[:1056], ignore_index=True)
        gload = gload.drop(gload.index[:1056])
        gas_load = pd.DataFrame(index=index)
        gas_load["SAT"] = gload["SAT"].values.repeat(res)

        pvgen = pd.read_csv(path + "pot_pv_timeseries_synth.csv")
        pvgen = pvgen.append(pvgen[:1056], ignore_index=True)
        pvgen = pvgen.drop(pvgen.index[:1056])
        pv = pd.Series(data=pvgen["p_max_pu"].values.repeat(res), index=index)

        wind = None

    else:
        if temporal != "hourly":
            print(" ")
            print(
                "Bei Verwendung der synthetischen Daten ist eine stündliche Auflösung vorgesehen."
            )
            print(" ")

        # bei Verwendung synthetischer Zeitreihen
        # in fester stündlicher Auflösung für 2019

        if args["scale_synth_to_real"]:
            el_loads = pd.read_csv(path + "el_load_synth_skal.csv").set_index("time")
            el_loads.index = pd.date_range(
                "2019-01-01 00:00", "2019-12-31 23:00", freq="H"
            )

        else:
            el_loads = pd.read_csv(path + "el_load_synth.csv").set_index("time")
            el_loads.index = pd.date_range(
                "2019-01-01 00:00", "2019-12-31 23:00", freq="H"
            )

        heat_load = pd.read_csv(path + "heat_load_synth.csv").set_index("time")
        heat_load.index = pd.date_range(
            "2019-01-01 00:00", "2019-12-31 23:00", freq="H"
        )

        gas_load = pd.read_csv(path + "gas_load_synth.csv").set_index("time")
        gas_load.index = pd.date_range("2019-01-01 00:00", "2019-12-31 23:00", freq="H")

        pv = pd.read_csv(path + "pot_pv_timeseries_synth.csv")
        pv = pd.Series(
            pv["p_max_pu"].values,
            index=pd.date_range("2019-01-01 00:00", "2019-12-31 23:00", freq="H"),
        )

        wind = None

        if args["IES_extension"]["extension"]:
            wind = pd.read_csv(path + "wind_timeseries_full.csv", sep=",")
            wind = pd.Series(
                wind["p_max_pu"].values,
                index=pd.date_range("2019-01-01 00:00", "2019-12-31 23:00", freq="H"),
            )

    return el_loads, heat_load, gas_load, pv, wind


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
    gas_load,
    pv,
    wind,
    args,
):
    network = pypsa.Network()
    use_real_data = args["use_real_data"]
    temporal = args["temporal_resolution"]

    if use_real_data:
        if temporal == "5min":
            args["start_hour"] = args["start_hour"] * 12
            args["end_hour"] = args["end_hour"] * 12
            sns = pd.date_range("2023-02-14 00:00", "2024-02-13 23:55", freq="5min")
            network.set_snapshots(sns[args["start_hour"] - 1 : args["end_hour"]])
            network.snapshot_weightings.objective = 1 / 12
            network.snapshot_weightings.stores = 1 / 12
            network.snapshot_weightings.generators = 1 / 12

        elif temporal == "15min":
            args["start_hour"] = args["start_hour"] * 4
            args["end_hour"] = args["end_hour"] * 4
            sns = pd.date_range("2023-02-14 00:00", "2024-02-13 23:45", freq="15min")
            network.set_snapshots(sns[args["start_hour"] - 1 : args["end_hour"]])
            network.snapshot_weightings.objective = 1 / 4
            network.snapshot_weightings.stores = 1 / 4
            network.snapshot_weightings.generators = 1 / 4

        else:
            sns = pd.date_range("2023-02-14 00:00", "2024-02-13 23:00", freq="H")
            network.set_snapshots(sns[args["start_hour"] - 1 : args["end_hour"]])

    else:
        sns = pd.date_range("2019-01-01 00:00", "2019-12-31 23:00", freq="H")
        network.set_snapshots(sns[args["start_hour"] - 1 : args["end_hour"]])

    # Buses

    if "geometry" in buses.columns:
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
    else:
        for i in range(0, len(buses)):
            bus = buses.iloc[i]
            network.add(
                "Bus",
                name=bus.name,
                carrier=bus.carrier,
                v_nom=bus.v_nom,
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
                p_nom_min=gen.p_nom_min,
                p_nom_max=gen.p_nom_max,
                p_nom_extendable=gen.p_nom_extendable,
                marginal_cost=gen.marginal_cost,
                capital_cost=gen.capital_cost,
                p_max_pu=pv,
            )
        elif gen.carrier == "Wind":
            network.add(
                "Generator",
                name=gen.name,
                carrier=gen.carrier,
                bus=gen.bus,
                control=gen.control,
                p_nom=gen.p_nom,
                p_nom_min=gen.p_nom_min,
                p_nom_max=gen.p_nom_max,
                p_nom_extendable=gen.p_nom_extendable,
                marginal_cost=gen.marginal_cost,
                capital_cost=gen.capital_cost,
                p_max_pu=wind,
            )
        else:
            network.add(
                "Generator",
                name=gen.name,
                carrier=gen.carrier,
                bus=gen.bus,
                control=gen.control,
                p_nom=gen.p_nom,
                p_nom_min=gen.p_nom_min,
                p_nom_max=gen.p_nom_max,
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
            p_nom_min=link.p_nom_min,
            efficiency=link.efficiency,
            marginal_cost=link.marginal_cost,
            capital_cost=link.capital_cost,
        )
        
    if args["IES_extension"]["electrolyser-extendable"]:
        network.links.loc['PtH2', 'p_nom_extendable'] = True 
        network.links.loc['PtH2', 'p_nom_min'] = 0 
        network.links.loc['PtH2+heat', 'capital_cost'] = 46763    # Masterarbeit L. Zimmermann (annualized)
        network.links.loc['PtH2+heat', 'p_nom'] = 0.25*(0.65/0.85)

        
    
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
        elif load.carrier == "heat":
            network.add(
                "Load",
                name=load.name,
                carrier=load.carrier,
                bus=load.bus,
                p_set=heat_load[load.name],
            )
        else:
            network.add(
                "Load",
                name=load.name,
                carrier=load.carrier,
                bus=load.bus,
                p_set=gas_load[load.name],
            )

    return network


def calc_flex_potentials(p, delta_t, s_util, s_dec, s_inc, s_flex):
    # nach Heitkoetter et. al (doi:https://doi.org/10.1016/j.adapen.2020.100001)

    l = p * s_flex  # scheduled load
    energy = l.sum()  # for max capacity
    cap = (energy * s_flex) / (8760 * s_util)  # max capacity
    pmax = cap * s_inc - l
    pmax[pmax < 0] = 0
    pmin = -(l - cap * s_dec)
    pmin[pmin > 0] = 0
    emax = l.copy()
    emin = l.copy()

    # Berechnung der Potentiale

    for col in l.columns:
        for i in range(len(l[col])):
            if i + delta_t > len(l[col]) - 1:
                emax.at[emax.index[i], col] = (
                    l.loc[l.index[i:]][col].sum()
                    + l.loc[l.index[: delta_t - (len(l[col]) - i)]][col].sum()
                )
            else:
                emax.at[emax.index[i], col] = l.loc[l.index[i] : l.index[i + delta_t]][
                    col
                ].sum()
            if i - delta_t < 0:
                emin.at[emin.index[i], col] = -1 * (
                    l.loc[l.index[:i]][col].sum()
                    + l.loc[l.index[len(l[col]) - delta_t + i :]][col].sum()
                )
            else:
                emin.at[emin.index[i], col] = (
                    -1 * l.loc[l.index[i - delta_t] : l.index[i]][col].sum()
                )

    pnom = pd.DataFrame(
        {"pmax": pmax.max(), "pmin": abs(pmin.min())}, index=pmax.columns
    )
    pnom = pnom.max(axis=1)
    enom = pd.DataFrame(
        {"emax": emax.max(), "emin": abs(emin.min())}, index=emax.columns
    )
    enom = enom.max(axis=1)

    return pmax, pmin, emax, emin, pnom, enom


def emob_potentials(network):
    # Implementierung nach Heitkoetter et. al (doi:https://doi.org/10.1016/j.adapen.2020.100001)

    ls = network.loads.index[network.loads.index.str.startswith("LS")]
    p = network.loads_t.p_set[ls]

    ## Parametrisierung nach Heitkoetter et. al (doi:https://doi.org/10.1016/j.adapen.2020.100001)
    pmax, pmin, emax, emin, pnom, enom = calc_flex_potentials(p, 5, 0.07, 0, 0.25, 1)
    pmax[
        pmax < 0.00001
    ] = 0  # vernachlässigbare Potentiale (< durch 0 ersetzen für bessere Lösbarkeit
    pmin[pmin > -0.00001] = 0

    pmaxpu = pmax / pnom
    pminpu = pmin / pnom
    emaxpu = emax / enom
    eminpu = emin / enom

    for ev in ls:
        network.add(
            "Bus",
            name=ev + "_flex",
            carrier="AC",
            v_nom=0.4,
        )

        network.add(
            "Link",
            name=ev + "_flex",
            carrier="AC",
            bus0=ev,
            bus1=ev + "_flex",
            p_nom_extendable=False,
            p_nom=pnom[ev],
            p_min_pu=pminpu[ev],
            p_max_pu=pmaxpu[ev],
            efficiency=1,
            marginal_cost=0,
            capital_cost=0,
        )

        network.add(
            "Store",
            name=ev + "_flex",
            carrier="AC",
            bus=ev + "_flex",
            e_nom_extendable=False,
            e_nom=enom[ev],
            e_min_pu=eminpu[ev],
            e_max_pu=emaxpu[ev],
            standing_loss=0,
            e_cyclic=True,
            marginal_cost=0,
            capital_cost=0,
        )


def dsm_potentials(network):
    # Implementierung nach Heitkoetter et. al (doi:https://doi.org/10.1016/j.adapen.2020.100001)

    # 1) AN1: landwirtschaftlicher Betrieb

    # 2) weitere AN (normale Haushalte)

    an = network.loads.index[
        network.loads.index.str.startswith("AN")
        | network.loads.index.str.startswith("KN")
    ]
    # an = an.drop('AN1')

    ## zeitabhängige Potentiale verschiedener Anwendungen berechnen
    ## Parametrisierung nach Heitkoetter et. al (doi:https://doi.org/10.1016/j.adapen.2020.100001)

    p = network.loads_t.p_set[an]
    # Wasch- und Trocknungsvorgänge
    p1 = p * 0.09
    pmax1, pmin1, emax1, emin1, pnom1, enom1 = calc_flex_potentials(
        p1, 6, 0.01, 0.0025, 0.025, 0.4
    )
    # Kühlprozesse
    p2 = p * 0.17
    pmax2, pmin2, emax2, emin2, pnom2, enom2 = calc_flex_potentials(
        p2, 2, 0.33, 0, 1, 0.4
    )

    ## zeitabhängige Potentiale pro AN aufaddieren und für Komponenten vorbereiten

    pmax = pmax1 + pmax2
    pmin = pmin1 + pmin2
    emax = emax1 + emax2
    emin = emin1 + emin2
    pmax[
        pmax < 0.00001
    ] = 0  # vernachlässigbare Potentiale durch 0 ersetzen für bessere Lösbarkeit
    pmin[pmin > -0.00001] = 0
    pnom = pd.DataFrame(
        {"pmax": pmax.max(), "pmin": abs(pmin.min())}, index=pmax.columns
    )
    pnom = pnom.max(axis=1)
    enom = pd.DataFrame(
        {"emax": emax.max(), "emin": abs(emin.min())}, index=emax.columns
    )
    enom = enom.max(axis=1)
    pmaxpu = pmax / pnom
    pminpu = pmin / pnom
    emaxpu = emax / enom
    eminpu = emin / enom

    ## Komponenten mit zeitabhängigen Potentialen hinzufügen

    for house in an:
        network.add(
            "Bus",
            name=house + "_DSM",
            carrier="AC",
            v_nom=0.4,
        )

        network.add(
            "Link",
            name=house + "_dsm",
            carrier="AC",
            bus0=house,
            bus1=house + "_DSM",
            p_nom_extendable=False,
            p_nom=pnom[house],
            p_min_pu=pminpu[house],
            p_max_pu=pmaxpu[house],
            efficiency=1,
            marginal_cost=0,
            capital_cost=0,
        )

        network.add(
            "Store",
            name=house + "_dsm",
            carrier="AC",
            bus=house + "_DSM",
            e_nom_extendable=False,
            e_nom=enom[house],
            e_min_pu=eminpu[house],
            e_max_pu=emaxpu[house],
            standing_loss=0,
            e_cyclic=True,
            marginal_cost=0,
            capital_cost=0,
        )


def adapt_settings(network, args):
    if args["IES_extension"]["extension"]:
        print(" ")
        print(
            "Hinweis: Bei der Erweiterung des IES um den Ortsteil Dörpum werden die elekrischen Leitungen ausbaubar abgebildet."
        )
        print(" ")

        if args["IES_extension"]["electrolyser-prio"]:
            print(" ")
            print(
                "Hinweis: Bei der Priorisierung der Bedienung des Elektrolyseurs, wird automatisch ein Batteriespeicher am Elektrolyseur mit optimiert."
            )
            print(" ")
            network.storage_units.at["BSp_Wind", "p_nom_extendable"] = True
            
    # Flexibilitätspotentiale

    if "emob" in args["flexible_components"]:
        emob_potentials(network)

    if "dsm" in args["flexible_components"]:
        dsm_potentials(network)

    # ausbaubare Komponenten

    if "el_lines" in args["extendable_components"]:
        network.lines.s_nom_extendable = True

    if "wind" in args["extendable_components"]:
        network.generators.loc[
            network.generators[network.generators.carrier == "Wind"].index,
            "p_nom_extendable",
        ] = True

    if "pv" in args["extendable_components"]:
        network.generators.loc[
            network.generators[network.generators.carrier == "PV"].index,
            "p_nom_extendable",
        ] = True

    if "batteries" in args["extendable_components"]:
        network.storage_units.p_nom_extendable = True

    if "heat-store" in args["extendable_components"]:
        network.stores.at["WSp", "e_nom_extendable"] = True

    return network
