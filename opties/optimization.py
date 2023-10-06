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
This file contains the functions related to the optimization.
"""

from pypsa.linopt import get_var, linexpr, define_constraints

__copyright__ = (
    "Europa-Universität Flensburg, Centre for Sustainable Energy Systems, "
    "FossilExit Research Group"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "KathiEsterl, mohsenmansouri"

def add_chp_constraints_nmp(n, sns):
    
    #import pdb; pdb.set_trace()
    
    # Konstanten
    c_m = 0.75 # backpressure limit
    c_v = 0.15 # marginal loss for each additional generation of heat

    # KWK: elektrische und Wärme-Links
    electric_bool = n.links.carrier == 'KWK_AC'
    heat_bool = n.links.carrier == 'KWK_heat'
    electric_links = n.links.index[electric_bool]
    heat_links = n.links.index[heat_bool]

    # Effizienzen Wärme-Links
    n.links.loc[heat_links, "efficiency"] = (n.links.loc[electric_links, "efficiency"] / c_v).values.mean()
    
    # KWK-Gasknoten
    ch4_nodes_with_chp = n.buses.loc[n.links[n.links.index.str.startswith('KWK')].bus0].index.unique()

    # Define the power variables for links and generators
    #link_p = get_var(n, "Link", "p")
    #gen_p = get_var(n, "Generator", "p")

    for i in ch4_nodes_with_chp:
        
        # Links an ausgewähltem Knoten
        elec = n.links[(n.links.carrier=='KWK_AC') & (n.links.bus0 == i)].index
        heat = n.links[(n.links.carrier=='KWK_W') & (n.links.bus0 == i)].index
        
        # Leistung an Links (Optimierungsvariable)
        link_p = get_var(n, "Link", "p")

        # Constraints ensuring that heat and electricity production don't exceed limits based on the biogas input
        lhs_1 = sum(c_m * n.links.at[h_chp, "efficiency"] * link_p[h_chp] for h_chp in heat)
        lhs_2 = sum(n.links.at[e_chp, "efficiency"] * link_p[e_chp] for e_chp in elec)
        
        lhs = linexpr((1, lhs_1), (-c_v, lhs_2))
        define_constraints(n, lhs, "<=", 0, "chplink_" + str(i), "backpressure")

        # top_iso_fuel_line
        lhs, *ax = linexpr(
            (1, sum(link_p[h_chp] for h_chp in heat)),
            (1, sum(link_p[h_e] for h_e in elec)),
            return_axes=True,
        )

        define_constraints(
            n,
            lhs,
            "<=",
            n.links.loc[elec].p_nom.sum(),
            "chplink_" + str(i),
            "top_iso_fuel_line_fix",
            axes=ax,
        )
    
class Constraints:

    def extra_functionalities(self, network, snapshots):
        """Add constraints to pypsa-model using extra-functionality.

        Parameters
        ----------
        network : :class:`pypsa.Network`
            Overall container of PyPSA
        snapshots : pandas.DatetimeIndex
            List of timesteps considered in the optimization

        """
        add_chp_constraints_nmp(network, snapshots)
