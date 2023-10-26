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
This file contains the functions to examine the optimization results.
"""

import pandas as pd

__copyright__ = (
    "Europa-Universität Flensburg, Centre for Sustainable Energy Systems, "
    "FossilExit Research Group"
)
__license__ = "GNU Affero General Public License Version 3 (AGPL-3.0)"
__author__ = "KathiEsterl"


def calc_investment_cost(network):
    # elektrisches Netz: AC-lines & DC-lines

    network_costs = [0, 0]

    ext_lines = network.lines[network.lines.s_nom_extendable]
    ext_trafos = network.transformers[network.transformers.s_nom_extendable]
    ext_links = network.links[network.links.p_nom_extendable]
    ext_dc_lines = ext_links[ext_links.carrier == "DC"]

    if not ext_lines.empty:
        network_costs[0] = (
            (ext_lines.s_nom_opt - ext_lines.s_nom_min) * ext_lines.capital_cost
        ).sum()

    if not ext_trafos.empty:
        network_costs[0] = (
            network_costs[0]
            + (
                (ext_trafos.s_nom_opt - ext_trafos.s_nom) * ext_trafos.capital_cost
            ).sum()
        )

    if not ext_dc_lines.empty:
        network_costs[1] = (
            (ext_dc_lines.p_nom_opt - ext_dc_lines.p_nom_min)
            * ext_dc_lines.capital_cost
        ).sum()

    # diverse Link-Komponenten

    link_costs = 0

    ext_links = ext_links[ext_links.carrier != "DC"]

    if not ext_links.empty:
        link_costs = (
            (ext_links.p_nom_opt - ext_links.p_nom_min) * ext_links.capital_cost
        ).sum()

    # Batteriespeicher, Wärmespeicher, Biogasspeicher

    sto_costs = [0, 0, 0]

    ext_storage = network.storage_units[network.storage_units.p_nom_extendable]
    ext_store = network.stores[network.stores.e_nom_extendable]

    if not ext_storage.empty:
        sto_costs[0] = (
            (ext_storage.p_nom_opt - ext_storage.p_nom_min) * ext_storage.capital_cost
        ).sum()

    if not ext_store.empty:
        heat = ext_store[ext_store.index == "WSp"]
        sto_costs[1] = ((heat.e_nom_opt - heat.e_nom_min) * heat.capital_cost).sum()
        gas = ext_store[ext_store.index == "GSp"]
        sto_costs[1] = ((gas.e_nom_opt - gas.e_nom_min) * gas.capital_cost).sum()

    return network_costs, link_costs, sto_costs


def calc_marginal_cost(network):
    gen = (
        network.generators_t.p.mul(network.snapshot_weightings.objective, axis=0)
        .sum(axis=0)
        .mul(network.generators.marginal_cost)
        .sum()
    )

    link = (
        abs(network.links_t.p0)
        .mul(network.snapshot_weightings.objective, axis=0)
        .sum(axis=0)
        .mul(network.links.marginal_cost)
        .sum()
    )

    stor = (
        network.storage_units_t.p.mul(network.snapshot_weightings.objective, axis=0)
        .sum(axis=0)
        .mul(network.storage_units.marginal_cost)
        .sum()
    )

    marginal_cost = gen + link + stor

    return marginal_cost


def calc_network_expansion(network):
    lines = (network.lines.s_nom_opt - network.lines.s_nom_min)[
        network.lines.s_nom_extendable
    ]

    ext_links = network.links[network.links.p_nom_extendable]
    ext_dc_lines = ext_links[ext_links.carrier == "DC"]

    dc_links = ext_dc_lines.p_nom_opt - ext_dc_lines.p_nom_min

    return lines, dc_links


def calc_results(network):
    results = pd.DataFrame(
        columns=["unit", "value"],
        index=[
            "annualisierte Systemkosten",
            "annualisierte Investkosten",
            "annualisierte marginale Kosten",
            "Investkosten: ",
            "annualisierte Investkosten elektrisches Netz",
            "annualisierte Investkosten Batteriespeicher",
            "annualisierte Investkosten Wärmespeicher",
            "annualisierte Investkosten Biogasspeicher",
            "annualisierte Investkosten diverser Link-Komponenten",  # Links Wärmespeicher, Links Abwärme und Netzanschluss
            "Ausbau: ",
            "rel. Netzausbau",
            "abs. Netzausbau",
            "Ausbau Batteriespeicher",
            "Ausbau Wärmespeicher",
            "Ausbau Gasspeicher",
            "Betriebskosten: ",
            "Erträge aus Trocknungsanlage",
            "Erträge aus Netzeinspeisung",
            "Kosten aus Netzbezug",
            "Kosten aus Betrieb der BHKWs (inklusive Biogas)",
            "Betrieb: ",
            "Biogaserzeugung",
            "gesamte elektrische Last",
            "Erzeugung aus PV-Anlagen",
            "Erzeugung durch BHKW - Strom",
            "Netzbezug",
            "Netzeinspeisung",
            "gesamte Wärmelast",
            "Last der Trocknungsanlage",
            "restliche Abwärme",
            "Erzeugung durch BHKW - Wärme",
            "Erzeugung durch Spitzenlastkessel",
        ],
    )

    results.unit[results.index.str.contains("Netzbezug")] = "MWh"
    results.unit[results.index.str.contains("Netzeinspeisung")] = "MWh"
    results.unit[results.index.str.contains("Kosten")] = "EUR/a"
    results.unit[results.index.str.contains("kosten")] = "EUR/a"
    results.unit[results.index.str.contains("Erträge")] = "EUR/a"
    results.unit[results.index.str.contains("Ausbau")] = "MW"
    results.unit[results.index.str.contains("ausbau")] = "MW"
    results.unit[results.index.str.contains("Last")] = "MWh"
    results.unit[results.index.str.contains("last")] = "MWh"
    results.unit[results.index.str.contains("restlich")] = "MWh"
    results.unit[results.index.str.contains("Erzeugung")] = "MWh"
    results.unit[results.index.str.contains("erzeugung")] = "MWh"
    results.unit[results.index.str.contains("rel.")] = "p.u."
    results.unit[results.index.str.contains(":")] = "-"
    results.value[results.index.str.contains(":")] = "-"

    # Systemkosten

    results.value["annualisierte Systemkosten"] = network.objective

    # Investkosten

    invest = calc_investment_cost(network)

    results.value["annualisierte Investkosten"] = (
        sum(invest[0]) + invest[1] + sum(invest[2])
    )

    results.value["annualisierte Investkosten elektrisches Netz"] = sum(invest[0])

    results.value["annualisierte Investkosten Batteriespeicher"] = invest[2][0]

    results.value["annualisierte Investkosten Wärmespeicher"] = invest[2][1]

    results.value["annualisierte Investkosten Biogasspeicher"] = invest[2][2]

    results.value["annualisierte Investkosten diverser Link-Komponenten"] = invest[1]

    # marginale Kosten

    results.value["annualisierte marginale Kosten"] = calc_marginal_cost(network)

    results.value["Erträge aus Trocknungsanlage"] = network.links_t.p0["TA"].mul(
        network.snapshot_weightings.objective, axis=0
    ).sum() * (network.links.loc["TA"].marginal_cost)

    results.value["Erträge aus Netzeinspeisung"] = network.links_t.p0["NA_Sp"].mul(
        network.snapshot_weightings.objective, axis=0
    ).sum() * (network.links.loc["NA_Sp"].marginal_cost)

    results.value["Kosten aus Netzbezug"] = network.generators_t.p["NeAn"].mul(
        network.snapshot_weightings.objective, axis=0
    ).sum() * (network.generators.loc["NeAn"].marginal_cost)

    results.value["Kosten aus Betrieb der BHKWs (inklusive Biogas)"] = (
        network.generators_t.p["BGA1"]
        .mul(network.snapshot_weightings.objective, axis=0)
        .sum()
        * (network.generators.loc["BGA1"].marginal_cost)
        + network.generators_t.p["BGA2"]
        .mul(network.snapshot_weightings.objective, axis=0)
        .sum()
        * (network.generators.loc["BGA2"].marginal_cost)
        + (
            network.links_t.p0[network.links[network.links.carrier == "KWK_AC"].index]
            .mul(network.snapshot_weightings.objective, axis=0)
            .sum()
            * (network.links[network.links.carrier == "KWK_AC"].marginal_cost)
        ).sum()
    )

    # Systemausbau

    results.value["abs. Netzausbau"] = (
        calc_network_expansion(network)[0].sum()
        - calc_network_expansion(network)[0][10]
    )

    ext_lines = network.lines[network.lines.s_nom_extendable]
    results.value["rel. Netzausbau"] = (
        calc_network_expansion(network)[0].sum()
        - calc_network_expansion(network)[0][10]
    ) / ext_lines.s_nom.sum()

    results.value["Ausbau Batteriespeicher"] = (
        (network.storage_units.p_nom_opt - network.storage_units.p_nom_min)[
            network.storage_units.p_nom_extendable
        ]
        .groupby(network.storage_units.carrier)
        .sum()
        .sum()
    )

    results.value["Ausbau Wärmespeicher"] = (
        network.stores.e_nom_opt - network.stores.e_nom_min
    )[network.stores.index == "WSp"].sum()

    results.value["Ausbau Gasspeicher"] = (
        network.stores.e_nom_opt - network.stores.e_nom_min
    )[network.stores.index == "GSp"].sum()

    # Systemversorgung

    results.value["gesamte elektrische Last"] = (
        network.loads_t.p[network.loads[network.loads.carrier == "AC"].index]
        .sum()
        .sum()
    )

    results.value["gesamte Wärmelast"] = (
        network.loads_t.p[network.loads[network.loads.carrier == "heat"].index]
        .sum()
        .sum()
    )

    results.value["Erzeugung aus PV-Anlagen"] = (
        network.generators_t.p[
            network.generators[network.generators.carrier == "PV"].index
        ]
        .sum()
        .sum()
    )

    results.value["Erzeugung durch BHKW - Strom"] = abs(
        network.links_t.p1[network.links[network.links.carrier == "KWK_AC"].index]
        .sum()
        .sum()
    )

    results.value["Erzeugung durch BHKW - Wärme"] = abs(
        network.links_t.p1[network.links[network.links.carrier == "KWK_heat"].index]
        .sum()
        .sum()
    )

    results.value["Erzeugung durch Spitzenlastkessel"] = network.generators_t.p[
        "SpK"
    ].sum()

    results.value["Last der Trocknungsanlage"] = network.links_t.p0["TA"].sum()

    results.value["restliche Abwärme"] = network.links_t.p0["Abw"].sum()

    results.value["Netzbezug"] = network.generators_t.p["NeAn"].sum()

    results.value["Netzeinspeisung"] = network.links_t.p0["NA_Sp"].sum()

    results.value["Biogaserzeugung"] = (
        network.generators_t.p["BGA1"].sum() + network.generators_t.p["BGA2"].sum()
    )

    return results
