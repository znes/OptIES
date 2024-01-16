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
__author__ = "KathiEsterl, MatthiasW"


def import_data(path='data/'):
    
    # Import von Komponenten aus csv-Dateien
       
    buses = pd.read_csv(path+'buses.csv').set_index('name')
    buses['geometry'] = buses['geometry'].apply(shapely.wkt.loads)
    buses = gpd.GeoDataFrame(buses, geometry = 'geometry')
    
    buses_fw_erw = pd.read_csv(path+'Erw/buses_fw_erw_nur.csv').set_index('name')
    buses_fw_erw['geometry'] = buses_fw_erw['geometry'].apply(shapely.wkt.loads)
    buses_fw_erw = gpd.GeoDataFrame(buses_fw_erw, geometry = 'geometry')
    
    lines = pd.read_csv(path+'lines.csv').set_index('id')    
    generators = pd.read_csv(path+'generators5000.csv', delimiter=";").set_index('name')
    
    storage_units = pd.read_csv(path+'storage_units.csv', delimiter=";").set_index('name')
    
    stores = pd.read_csv(path+'stores_t2.csv', delimiter=";").set_index('name')
    
    links = pd.read_csv(path+'links.csv', delimiter=";").set_index('name')
    links_fw_erw = pd.read_csv(path+'Erw/links_fw_erw_nur.csv', delimiter=";").set_index('name')

    loads = pd.read_csv(path+'loads_fw_erw.csv').set_index('name')
    loads = loads.drop(['LS1', 'LS2']) # TODO: noch ohne E-Mob

    #th_loads = pd.read_csv(path+'Erw/th_loads.csv').set_index('name')
    #th_loads_Ausbau = pd.read_csv(path+'Erw/th_loads_Ausbau.csv', delimiter=",").set_index('name')

    return buses, buses_fw_erw, lines, generators, storage_units, stores, links, links_fw_erw, loads

def import_timeseries(path='data/timeseries/'):
    
    el_profiles = pd.read_csv(path+'el_load_synth.csv', index_col=0)
    el_profiles.index = pd.date_range("2019-01-01 00:00","2019-12-31 23:00",freq="H")
    #el_profiles = el_profiles / 1000
    
    #th_profiles = pd.read_csv(path+'th_load+losses_a.csv', index_col=0, delimiter=";")
    #th_profiles.index = pd.date_range("2019-01-01 00:00","2019-12-31 23:00",freq="H")
    #th_profiles = th_profiles / 1000
    
    th_new_profiles = pd.read_csv(path+'th_load+losses_nn.csv', index_col=0, delimiter=";")
    th_new_profiles.index = pd.date_range("2019-01-01 00:00","2019-12-31 23:00",freq="H")
    th_new_profiles = th_new_profiles / 1000    
    
    gas_profile = pd.read_csv(path + "gas_load.csv", delimiter=",").set_index("time")
    gas_profile.index = pd.date_range("2019-01-01 00:00", "2019-12-31 23:00", freq="H")
    
    pv = pd.read_csv(path+'pv_timeseries.csv')
    pv = pd.Series(
        pv['p_max_pu'].values, 
        index=pd.date_range("2019-01-01 00:00","2019-12-31 23:00",freq="H")
    )
    
    return el_profiles, th_new_profiles, gas_profile, pv


def create_pypsa_network(
    buses, 
    buses_fw_erw, 
    lines, 
    generators, 
    storage_units, 
    stores, 
    links,
    links_fw_erw, 
    loads, 
    el_profiles,  
    th_new_profiles,
    gas_profile,
    pv
):
    
    network = pypsa.Network() 
    
    network.set_snapshots(pd.date_range(
    "2019-01-01 00:00","2019-12-31 23:00",freq="H"))

    # Buses
    
    for i in range(0, len(buses)):
        bus = buses.iloc[i]
        network.add(
            "Bus", 
            name=bus.name, 
            carrier=bus.carrier, 
            v_nom=bus.v_nom, 
            x=shapely.get_x(bus.geometry), 
            y=shapely.get_y(bus.geometry)
        )
    
    for i in range(0, len(buses_fw_erw)):
        bus = buses_fw_erw.iloc[i]
        network.add(
            "Bus", 
            name=bus.name, 
            carrier=bus.carrier, 
            x=shapely.get_x(bus.geometry), 
            y=shapely.get_y(bus.geometry), 
            v_nom=bus.v_nom
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
            capital_cost=line.capital_cost
        )
    
    # Generation
    
    for i in range(0, len(generators)):
        gen = generators.iloc[i]
        if gen.carrier=='PV':
            network.add(
                "Generator", 
                name = gen.name, 
                carrier=gen.carrier, 
                bus=gen.bus, 
                control=gen.control, 
                p_nom=gen.p_nom,
                p_nom_min=gen.p_nom_min,
                p_nom_max=gen.p_nom_max,
                p_nom_extendable=gen.p_nom_extendable, 
                marginal_cost=gen.marginal_cost, 
                capital_cost=gen.capital_cost, 
                p_max_pu=pv
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
                capital_cost=gen.capital_cost
            )
    
    # Storage Units
    
    for i in range(0, len(storage_units)):
        sto = storage_units.iloc[i]
        network.add(
            "StorageUnit", 
            name = sto.name, 
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
            capital_cost=sto.capital_cost
        )
    
    # Stores
    
    for i in range(0, len(stores)):
        sto = stores.iloc[i]
        network.add(
            "Store", 
            name = sto.name, 
            carrier=sto.carrier, 
            bus=sto.bus, 
            e_nom_extendable=sto.e_nom_extendable, 
            e_nom=sto.e_nom,  
            e_nom_min=sto.e_nom_min,
            e_nom_max=sto.e_nom_max, 
            standing_loss=sto.standing_loss, 
            e_cyclic=sto.e_cyclic, 
            marginal_cost=sto.marginal_cost, 
            capital_cost=sto.capital_cost
        )
    
    # Links
    
    for i in range(0, len(links)):
        link = links.iloc[i]
        network.add(
            "Link", 
            name = link.name, 
            carrier=link.carrier, 
            bus0=link.bus0, 
            bus1=link.bus1, 
            p_nom_extendable=link.p_nom_extendable, 
            p_nom=link.p_nom,
            #p_nom_min=link.p_nom_min,
            #p_nom_max=link.p_nom_max,
            efficiency=link.efficiency, 
            marginal_cost=link.marginal_cost, 
            capital_cost=link.capital_cost
        )

    for i in range(0, len(links_fw_erw)):
        link = links_fw_erw.iloc[i]
        network.add(
            "Link", 
            name = link.name, 
            bus0=link.bus0, 
            bus1=link.bus1, 
            p_nom_extendable=link.p_nom_extendable, 
            p_nom=link.p_nom, 
            p_nom_min=link.p_nom_min,
            #p_nom_max=link.p_nom_max,
            length = link.length, 
            marginal_cost=link.marginal_cost, 
            capital_cost=link.capital_cost
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
                p_set=el_profiles[load.bus],
            )
        elif load.carrier == "heat":
            network.add(
                "Load",
                name=load.name,
                carrier=load.carrier,
                bus=load.bus,
                p_set=th_new_profiles[load.name],
            )
        else:
            network.add(
                "Load",
                name=load.name,
                carrier=load.carrier,
                bus=load.bus,
                p_set=gas_profile[load.name],            
            )
             
    return network
