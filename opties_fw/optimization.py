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
import math
from pypsa.linopt import get_var, linexpr, define_constraints
from pyomo.environ import Constraint

__copyright__ = (
    "Europa-Universität Flensburg, Centre for Sustainable Energy Systems, "
    "FossilExit Research Group"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "KathiEsterl, mohsenmansouri"


def optimization(network, args):
    method = args["method"]
    path = args["csv_export"]

    # Effizienzen der Wärme-Links der KWK-Anlagen an extra KWK-Constraints anpassen
    # (bevor pyomo.model erstellt wird an dieser Stelle)
    c_v = 0.2  # marginal loss for each additional generation of heat
    # KWK: elektrische und Wärme-Links
    electric_bool = network.links.carrier == "KWK_AC"
    heat_bool = network.links.carrier == "KWK_heat"
    electric_links = network.links.index[electric_bool]
    heat_links = network.links.index[heat_bool]
    # Effizienzen Wärme-Links
    network.links.loc[heat_links, "efficiency"] = (
        network.links.loc[electric_links, "efficiency"] / c_v
    ).values.mean()

    ext = network.lines[network.lines.s_nom_extendable]

    if not ext.empty:
        # s_nom_pre = s_nom_opt of previous iteration
        l_snom_pre = network.lines.s_nom.copy()

        # calculate fixed number of iterations
        n_iter = method["n_iter"]

        for i in range(1, (1 + n_iter)):
            run_lopf(network, args, Constraints(args).extra_functionalities)

            path_it = path + "/lopf_iteration_" + str(i)
            network.export_to_csv_folder(path_it)

            # adapt s_nom per iteration
            if i < n_iter:
                network.lines.loc[network.lines.s_nom_extendable].x = (
                    network.lines.x * l_snom_pre / network.lines.s_nom_opt
                )

                network.lines.loc[network.lines.s_nom_extendable].r = (
                    network.lines.r * l_snom_pre / network.lines.s_nom_opt
                )

                network.lines.loc[network.lines.s_nom_extendable].g = (
                    network.lines.g * network.lines.s_nom_opt / l_snom_pre
                )

                network.lines.loc[network.lines.s_nom_extendable].b = (
                    network.lines.b * network.lines.s_nom_opt / l_snom_pre
                )

                # Set snom_pre to s_nom_opt for next iteration
                l_snom_pre = network.lines.s_nom_opt.copy()

    else:
        run_lopf(network, args, Constraints(args).extra_functionalities)


def run_lopf(network, args, extra_functionality):
    x = time.time()

    # snapshots
    start = args["start_snapshot"] - 1
    end = args["end_snapshot"]

    network.lopf(
        snapshots=network.snapshots[start:end],
        pyomo=args["method"]["pyomo"],
        solver_name=args["solver_name"],
        solver_options=args["solver_options"],
        extra_functionality=extra_functionality,
    )

    if math.isnan(network.objective):
        raise Exception("LOPF nicht gelöst.")

    y = time.time()
    z = (y - x) / 60

    print("Time for LOPF [min]:", round(z, 2))

    network.export_to_csv_folder(args["csv_export"])


def kwk_constraints_nmp(n, sns):
    # Konstanten
    nom_r = 1  # ratio between max heat output and max electric output
    c_m = 0.75  # backpressure limit
    # c_v = 0.2  # marginal loss for each additional generation of heat
    # Effizienzen der Wärme-Links bereits im Vorwege angepasst (bevor pyomo.model erstellt wird)

    # KWK: elektrische und Wärme-Links
    electric_bool = n.links.carrier == "KWK_AC"
    heat_bool = n.links.carrier == "KWK_heat"
    electric_links = n.links.index[electric_bool]
    heat_links = n.links.index[heat_bool]

    # Zusammengehörigkeit der elektrischen und Wärme-Links
    el_ht = {"KWK1_AC": "KWK1_W", "KWK2_AC": "KWK2_W", "KWK3_AC": "KWK3_W"}

    # bei Ausbau der BHKWs

    if n.links.loc[electric_links, "p_nom_extendable"].any():
        link_pnom = get_var(n, "Link", "p_nom")

        for elec in electric_links:
            heat = el_ht[elec]

            lhs1 = n.links.loc[elec, "efficiency"] * nom_r * link_pnom[elec]
            lhs2 = n.links.loc[heat, "efficiency"] * link_pnom[heat]

            lhs = linexpr((1, lhs1), (-1, lhs2))
            define_constraints(n, lhs, "==", 0, "heat-power output proportionality")

    # Leistung an Links (Optimierungsvariable)
    link_p = get_var(n, "Link", "p")

    for el in electric_links:
        ht = el_ht[el]

        # Verhältnis aus Strom- und Wärmeoutput

        lhs_1 = c_m * n.links.at[ht, "efficiency"] * link_p[ht]
        lhs_2 = n.links.at[el, "efficiency"] * link_p[el]

        lhs = linexpr((1, lhs_1), (-1, lhs_2))
        define_constraints(n, lhs, "<=", 0, "chplink_" + str(el), "backpressure")

        # Constraints zur Begrenzung des Biogaseinsatzes für Strom- und Wärmeoutput
        # top_iso_fuel_line

        lhs, *ax = linexpr(
            (1, link_p[ht]),
            (1, link_p[el]),
            return_axes=True,
        )

        define_constraints(
            n,
            lhs,
            "<=",
            n.links.loc[el].p_nom.sum(),
            "chplink_" + str(el),
            "top_iso_fuel_line_fix",
            axes=ax,
        )


def kwk_constraints_pyomo(n, sns):
    # Konstanten
    nom_r = 1  # ratio between max heat output and max electric output
    c_m = 0.75  # backpressure limit
    # c_v = 0.2  # marginal loss for each additional generation of heat
    # Effizienzen der Wärme-Links bereits im Vorwege angepasst (bevor pyomo.model erstellt wird)

    # KWK: elektrische und Wärme-Links
    electric_bool = n.links.carrier == "KWK_AC"
    heat_bool = n.links.carrier == "KWK_heat"
    electric_links = n.links.index[electric_bool]
    heat_links = n.links.index[heat_bool]

    # Zusammengehörigkeit der elektrischen und Wärme-Links
    el_ht = {"KWK1_AC": "KWK1_W", "KWK2_AC": "KWK2_W", "KWK3_AC": "KWK3_W"}

    # bei Ausbau der BHKWs
    if n.links.loc[electric_links, "p_nom_extendable"].any():
        for elec in electric_links:
            heat = el_ht[elec]

            def heat_power_output(model):
                lhs = n.links.at[elec, "efficiency"] * nom_r * model.link_p_nom[elec]
                rhs = n.links.at[heat, "efficiency"] * model.link_p_nom[heat]

                return lhs - rhs == 0

            setattr(
                n.model,
                "heat-power output proportionality" + str(elec),
                Constraint(rule=heat_power_output),
            )

    for el in electric_links:
        ht = el_ht[el]

        # Verhältnis aus Strom- und Wärmeoutput

        def backpressure(model, snapshot):
            lhs = c_m * n.links.at[ht, "efficiency"] * model.link_p[ht, snapshot]

            rhs = n.links.at[el, "efficiency"] * model.link_p[el, snapshot]

            return lhs <= rhs

        setattr(
            n.model,
            "backpressure_" + str(el),
            Constraint(list(sns), rule=backpressure),
        )

        # Constraints zur Begrenzung des Biogaseinsatzes für Strom- und Wärmeoutput
        # top_iso_fuel_line

        def top_iso_fuel_line(model, snapshot):
            lhs = (model.link_p[ht, snapshot]) + (model.link_p[el, snapshot])

            rhs = n.links.loc[el].p_nom.sum()

            return lhs <= rhs

        setattr(
            n.model,
            "top_iso_fuel_line_" + str(el),
            Constraint(list(sns), rule=top_iso_fuel_line),
        )


def trocknungsanlage_nmp(n, sns):
    store_e = get_var(n, "Store", "e").loc[sns[-1]]

    lhs = linexpr(
        (1, store_e["TA"]),
        return_axes=True,
    )

    define_constraints(
        n,
        lhs,
        "==",
        2976,
        "Store_TA",
        "load_trocknungsanlage",
    )


def trocknungsanlage_pyomo(n, sns):
    def load_trocknungsanlage(model, snapshot):
        lhs = n.model.store_e["TA", snapshot]
        rhs = 2976
#2121
        return lhs == rhs

    setattr(
        n.model,
        "load_trocknungsanlage",
        Constraint(sns[-1:], rule=load_trocknungsanlage),
    )


class Constraints:
    def __init__(self, args):
        self.args = args

    def extra_functionalities(self, network, snapshots):
        args = self.args

        if args["method"]["pyomo"]:
            kwk_constraints_pyomo(network, snapshots)
            trocknungsanlage_pyomo(network, snapshots)

        else:
            kwk_constraints_nmp(network, snapshots)
            trocknungsanlage_nmp(network, snapshots)
