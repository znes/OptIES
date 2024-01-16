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

import pypsa

from data_IES2 import import_data, import_timeseries, create_pypsa_network
from optimization import Constraints, optimization
from results_IES2 import calc_results

__copyright__ = (
    "Europa-Universität Flensburg, Centre for Sustainable Energy Systems, "
    "FossilExit Research Group"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "KathiEsterl, MatthiasW, mohsenmansouri"


args = {
    "path": "data/",
    "start_snapshot": 1,
    "end_snapshot": 8760,
    "method": {
        "type": "lopf",
        "n_iter": 2,
        "pyomo": True,
    },
    "solver_name": "gurobi",
    "solver_options": {
        "BarConvTol": 1e-05,
        "FeasibilityTol": 1e-05,
        "crossover": 0,
        "logFile": "solver_opties.log",
        "threads": 4,
        "method": 2,
        "BarHomogeneous": 1,
    },
    "csv_export": "opties_results",
}


buses, buses_IES2, lines, generators, storage_units, stores, links, loads = import_data(
    args["path"]
)

el_loads, heat_load, gas_load, pv, wind = import_timeseries(args["path"] + "/timeseries/")

network = create_pypsa_network(
    buses,
    buses_IES2,
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
)

#network.generators.p_nom_extendable = True

optimization(network, args)

results = calc_results(network)