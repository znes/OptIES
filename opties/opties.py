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
This is the application file for the tool OptIES.
"""

import time
import pandas as pd
import geopandas as gpd
import shapely
import pypsa

__copyright__ = (
    "Europa-Universität Flensburg, Centre for Sustainable Energy Systems, "
    "FossilExit Research Group"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "KathiEsterl, MatthiasW, mohsenmansouri"


# TODO:  

# check crs von buses

# standard line_type-Paramter während lopf angewandt?
# line_types spezifizieren für Leitungsparameter
# s_nom der Leitungen ableiten
# network.lines.num_parallel? undergrounding?!

# weitere Parametrisierung:  
    # siehe TODOS in prepare_data

# Verbesserung der Abbildung der Biogasanlage und KWK-Anlagen (siehe Notizen)

# Flexibilitäten
    # Flexpotential DSM an landwirtschaftlichem Betrieb
    # Lastzeitreihe und Flexpotential E-Mobilität

# plot network mit osm-background


def import_data(path='data/'):
    
    # Import von Komponenten aus csv-Dateien
       
    buses = pd.read_csv(path+'buses.csv').set_index('name')
    buses['geometry'] = buses['geometry'].apply(shapely.wkt.loads)
    buses = gpd.GeoDataFrame(buses, geometry = 'geometry')
    
    
    lines = pd.read_csv(path+'lines.csv').set_index('id')  
    generators = pd.read_csv(path+'generators.csv').set_index('name')
    storage_units = pd.read_csv(path+'storage_units.csv').set_index('name')
    stores = pd.read_csv(path+'stores.csv').set_index('name')
    links = pd.read_csv(path+'links.csv').set_index('name')
    loads = pd.read_csv(path+'loads.csv').set_index('name')
    
    loads = loads.drop(['LS1', 'LS2']) # TODO: noch ohne E-Mob

    return buses, lines, generators, storage_units, stores, links, loads

def import_timeseries(path='data/timeseries/'):
    
    el_loads = pd.read_csv(path+'el_load_synth.csv').set_index('time')
    el_loads.index = pd.date_range("2019-01-01 00:00","2019-12-31 23:00",freq="H")
    
    heat_load = pd.read_csv(path+'heat_load_synth.csv').set_index('time')
    heat_load.index = pd.date_range("2019-01-01 00:00","2019-12-31 23:00",freq="H")
    
    pv = pd.read_csv(path+'pv_timeseries.csv')
    pv = pd.Series(pv['p_max_pu'].values, index=pd.date_range("2019-01-01 00:00","2019-12-31 23:00",freq="H"))
    
    return el_loads, heat_load, pv


def create_pypsa_network(buses, lines, generators, storage_units, stores, links, loads, el_loads, heat_load, pv):
    
    network = pypsa.Network() 
    
    network.set_snapshots(pd.date_range(
    "2019-01-01 00:00","2019-12-31 23:00",freq="H"))

    # Buses
    
    for i in range(0, len(buses)):
        bus = buses.iloc[i]
        network.add("Bus", name=bus.name, carrier=bus.carrier, v_nom=bus.v_nom, x=shapely.get_x(bus.geometry), y=shapely.get_y(bus.geometry))
    
    # Lines
    
    for i in range(0, len(lines)):
        line = lines.iloc[i]
        network.add("Line", name=line.name, type=line.type, bus0=line.bus0, bus1=line.bus1, s_nom_extendable=line.s_nom_extendable, s_nom_min=line.s_nom_min, s_nom=line.s_nom, length=line.length, capital_cost=line.capital_cost)
    
    # Generation
    
    for i in range(0, len(generators)):
        gen = generators.iloc[i]
        if gen.carrier=='PV':
            network.add("Generator", name = gen.name, carrier=gen.carrier, bus=gen.bus, control=gen.control, p_nom=gen.p_nom, p_nom_extendable = gen.p_nom_extendable, marginal_cost=gen.marginal_cost, capital_cost=gen.capital_cost, p_max_pu=pv)
        else:
            network.add("Generator", name = gen.name, carrier=gen.carrier, bus=gen.bus, control=gen.control, p_nom=gen.p_nom, p_nom_extendable = gen.p_nom_extendable, marginal_cost=gen.marginal_cost, capital_cost=gen.capital_cost)
    
    # Storage Units
    
    for i in range(0, len(storage_units)):
        sto = storage_units.iloc[i]
        network.add("StorageUnit", name = sto.name, carrier=sto.carrier, bus=sto.bus, p_nom_extendable=sto.p_nom_extendable, p_nom=sto.p_nom, max_hours=sto.max_hours, standing_loss=sto.standing_loss, efficiency_store=sto.efficiency_store, efficiency_dispatch=sto.efficiency_dispatch, cyclic_state_of_charge=sto.cyclic_state_of_charge, marginal_cost=sto.marginal_cost, capital_cost=sto.capital_cost)
    
    # Stores
    
    for i in range(0, len(stores)):
        sto = stores.iloc[i]
        network.add("Store", name = sto.name, carrier=sto.carrier, bus=sto.bus, e_nom_extendable=sto.e_nom_extendable, e_nom=sto.e_nom, standing_loss=sto.standing_loss, e_cyclic=sto.e_cyclic, marginal_cost=sto.marginal_cost, capital_cost=sto.capital_cost)
    
    # Links
    
    for i in range(0, len(links)):
        link = links.iloc[i]
        network.add("Link", name = link.name, bus0=link.bus0, bus1=link.bus1, p_nom_extendable=link.p_nom_extendable, p_nom=link.p_nom, efficiency=link.efficiency, marginal_cost=link.marginal_cost, capital_cost=link.capital_cost)
    
    # Loads
    
    for i in range(0, len(loads)):
        load = loads.iloc[i]
        if load.carrier == 'AC':
            network.add("Load", name = load.name, carrier=load.carrier, bus=load.bus, p_set=el_loads[load.bus])
        else:
            network.add("Load", name = load.name, carrier=load.carrier, bus=load.bus, p_set=heat_load['aggregiert'])
     
    return network


def optimization(network, args):
    
    method = args['method']
    path = args["csv_export"]
    
    extra_functionality = None
    
    if network.lines.s_nom_extendable.any():
        
        # s_nom_pre = s_nom_opt of previous iteration
        l_snom_pre = network.lines.s_nom.copy()

        # calculate fixed number of iterations
        if "n_iter" in method:
            n_iter = method["n_iter"]

            for i in range(1, (1 + n_iter)):
                run_lopf(network, args, extra_functionality)

                path_it = path + "/lopf_iteration_" + str(i)
                network.export_to_csv_folder(path_it)

                # adapt s_nom per iteration
                if i < n_iter:
                    network.lines.x[network.lines.s_nom_extendable] = (
                        network.lines.x * l_snom_pre / network.lines.s_nom_opt
                    )

                    network.lines.r[network.lines.s_nom_extendable] = (
                        network.lines.r * l_snom_pre / network.lines.s_nom_opt
                    )

                    network.lines.g[network.lines.s_nom_extendable] = (
                        network.lines.g * network.lines.s_nom_opt / l_snom_pre
                    )

                    network.lines.b[network.lines.s_nom_extendable] = (
                        network.lines.b * network.lines.s_nom_opt / l_snom_pre
                    )

                    # Set snom_pre to s_nom_opt for next iteration
                    l_snom_pre = network.lines.s_nom_opt.copy()
                    t_snom_pre = network.transformers.s_nom_opt.copy()

        # TODO:  Version mit Threshold ?

    else:
        run_lopf(network, args, extra_functionality)

    
def run_lopf(network, args, extra_functionality):
    
    x = time.time()
    
    # snapshots
    start = args["start_snapshot"]-1
    end = args["end_snapshot"]
    
    network.lopf(
            snapshots=network.snapshots[start:end],
            pyomo=args["method"]["pyomo"],
            solver_name=args["solver_name"],
            solver_options=args["solver_options"],
            extra_functionality=extra_functionality
        )

    # TODO: Exception ?
    # TODO: pyomo vs. ohne pyomo unterscheiden ?
                
    y = time.time()
    z = (y - x) / 60

    print("Time for LOPF [min]:", round(z, 2))
    
    network.export_to_csv_folder(args["csv_export"])


##############################################################################################################################
    

args = {"path": 'data/',
        "start_snapshot": 1,
        "end_snapshot": 8760,
        "method": {  # Choose method and settings for optimization
            "type": "lopf",  # TODO ? 
            "n_iter": 2,  
            "pyomo": False,
        },
        "solver_name": "gurobi",
        "solver_options": {
            "BarConvTol": 1e-05,
            "FeasibilityTol": 1e-05,
            "crossover": 0,
            "logFile": "solver_opties.log",
            "threads": 4,
            "method": 2,
            "BarHomogeneous": 1
        },
        "csv_export": 'opties_results'}


buses, lines, generators, storage_units, stores, links, loads = import_data(args['path'])

el_loads, heat_load, pv = import_timeseries(args['path']+'/timeseries/')

network = create_pypsa_network(buses, lines, generators, storage_units, stores, links, loads, el_loads, heat_load, pv)

# TODO: manual fixes
network.generators.p_nom_extendable=False

optimization(network, args)

# network.plot(bus_sizes=0.00000001, line_widths=1, link_widths=1)





