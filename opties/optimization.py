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

import time
from pypsa.linopt import get_var, linexpr, define_constraints

__copyright__ = (
    "Europa-Universität Flensburg, Centre for Sustainable Energy Systems, "
    "FossilExit Research Group"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "KathiEsterl, mohsenmansouri"


def optimization(network, args):
    method = args["method"]
    path = args["csv_export"]

    # snapshots
    start = args["start_snapshot"] - 1
    end = args["end_snapshot"]
    snapshots = network.snapshots[start:end]

    if network.lines.s_nom_extendable.any():
        # s_nom_pre = s_nom_opt of previous iteration
        l_snom_pre = network.lines.s_nom.copy()

        # calculate fixed number of iterations
        if "n_iter" in method:
            n_iter = method["n_iter"]

            for i in range(1, (1 + n_iter)):
                run_lopf(network, args, Constraints().extra_functionalities)

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
        run_lopf(network, args, Constraints().extra_functionalities)


def run_lopf(network, args, extra_functionality):
    x = time.time()

    # snapshots
    start = args["start_snapshot"] - 1
    end = args["end_snapshot"]

    # network.optimize.create_model()

    network.lopf(
        snapshots=network.snapshots[start:end],
        pyomo=args["method"]["pyomo"],
        solver_name=args["solver_name"],
        solver_options=args["solver_options"],
        extra_functionality=extra_functionality,
    )

    # TODO: Exception ?
    # TODO: pyomo vs. ohne pyomo unterscheiden ?

    y = time.time()
    z = (y - x) / 60

    print("Time for LOPF [min]:", round(z, 2))

    network.export_to_csv_folder(args["csv_export"])


def add_chp_constraints_nmp(n, sns):
    # Konstanten
    c_m = 0.75  # backpressure limit
    c_v = 0.15  # marginal loss for each additional generation of heat

    # KWK: elektrische und Wärme-Links
    electric_bool = n.links.carrier == "KWK_AC"
    heat_bool = n.links.carrier == "KWK_heat"
    electric_links = n.links.index[electric_bool]
    heat_links = n.links.index[heat_bool]

    # Effizienzen Wärme-Links
    n.links.loc[heat_links, "efficiency"] = (
        n.links.loc[electric_links, "efficiency"] / c_v
    ).values.mean()

    # KWK-Gasknoten
    ch4_nodes_with_chp = n.buses.loc[
        n.links[n.links.index.str.startswith("KWK")].bus0
    ].index.unique()

    for i in ch4_nodes_with_chp:
        # Links an ausgewähltem Knoten
        elec = n.links[(n.links.carrier == "KWK_AC") & (n.links.bus0 == i)].index
        heat = n.links[(n.links.carrier == "KWK_heat") & (n.links.bus0 == i)].index

        # Leistung an Links (Optimierungsvariable)
        link_p = get_var(n, "Link", "p")

        # Verhältnis aus Strom- und Wärmeoutput

        lhs_1 = sum(
            c_m * n.links.at[h_chp, "efficiency"] * link_p[h_chp] for h_chp in heat
        )
        lhs_2 = sum(n.links.at[e_chp, "efficiency"] * link_p[e_chp] for e_chp in elec)

        lhs = linexpr((1, lhs_1), (-1, lhs_2))
        define_constraints(n, lhs, "<=", 0, "chplink_" + str(i), "backpressure")

        # Constraints zur Begrenzung des Biogaseinsatzes für Strom- und Wärmeoutput
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


# TODO: pyomo-constraints


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
