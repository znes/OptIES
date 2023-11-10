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
        sto_costs[2] = ((gas.e_nom_opt - gas.e_nom_min) * gas.capital_cost).sum()

    # Erzeugungseinheiten
    ext_gen = network.generators[network.generators.p_nom_extendable]

    if not ext_gen.empty:
        gen_costs = (
            (network.generators.p_nom_opt - network.generators.p_nom_min)
            * network.generators.capital_cost
        ).sum()
    else:
        gen_costs = 0

    return network_costs, link_costs, sto_costs, gen_costs


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
    ext_lines = network.lines[network.lines.s_nom_extendable]
    lines = ext_lines.s_nom_opt - ext_lines.s_nom_min

    ext_links = network.links[network.links.p_nom_extendable]
    ext_dc_lines = ext_links[ext_links.carrier == "DC"]
    dc_links = ext_dc_lines.p_nom_opt - ext_dc_lines.p_nom_min

    return lines, dc_links


def calc_results(network):
    results = pd.DataFrame(
        columns=["Einheit", "Wert"],
        index=[
            "Objective:",
            "Systemkosten: ",
            "annualisierte Systemkosten",
            "annualisierte Investkosten",
            "annualisierte marginale Kosten",
            "Investkosten: ",
            "annualisierte Investkosten elektrisches Netz",
            "annualisierte Investkosten PV-Anlagen",
            "annualisierte Investkosten Batteriespeicher",
            "annualisierte Investkosten Wärmespeicher",
            "annualisierte Investkosten Biogasspeicher",
            "annualisierte Investkosten diverser Link-Komponenten",  # Links Wärmespeicher, Links Abwärme und Netzanschluss
            "Ausbau: ",
            "rel. Netzausbau",
            "abs. Netzausbau",
            "Ausbau PV-Anlagen",
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
            "elektrischer Eigenverbrauch BGA",
            "elektrische Last IES",
            "Erzeugung aus PV-Anlagen",
            "Erzeugung durch BHKW - Strom",
            "Netzbezug",
            "Netzeinspeisung",
            "Wärmelast (Wärmenetz)",
            "Eigenverbrauch",
            "Last der Trocknungsanlage",
            "restliche Abwärme",
            "Erzeugung durch BHKW - Wärme",
            "Erzeugung durch Spitzenlastkessel",
        ],
    )

    results.Einheit[results.index.str.contains("Netzbezug")] = "MWh"
    results.Einheit[results.index.str.contains("Netzeinspeisung")] = "MWh"
    results.Einheit[results.index.str.contains("Kosten")] = "EUR/a"
    results.Einheit[results.index.str.contains("kosten")] = "EUR/a"
    results.Einheit[results.index.str.contains("Erträge")] = "EUR/a"
    results.Einheit[results.index.str.contains("Ausbau")] = "MW"
    results.Einheit[results.index.str.contains("ausbau")] = "MW"
    results.Einheit[results.index.str.contains("Last")] = "MWh"
    results.Einheit[results.index.str.contains("last")] = "MWh"
    results.Einheit[results.index.str.contains("verbrauch")] = "MWh"
    results.Einheit[results.index.str.contains("restlich")] = "MWh"
    results.Einheit[results.index.str.contains("Erzeugung")] = "MWh"
    results.Einheit[results.index.str.contains("erzeugung")] = "MWh"
    results.Einheit[results.index.str.contains("rel.")] = "p.u."
    results.Einheit[results.index.str.contains(":")] = "-"
    results.Wert[results.index.str.contains(":")] = "-"

    results.Wert["Objective"] = network.objective
    results.Einheit["Objective"] = '(€)'
    
    # TODO: post-ex Kostenberechnung für Spitzenlastkessel ?
    # da marginal_costs küsntlich erhöht um Einsatz zu verringern

    # Systemkosten
    
    invest = calc_investment_cost(network)
    
    marg = calc_marginal_cost(network)

    results.Wert["annualisierte Systemkosten"] = (sum(invest[0]) + invest[1] + sum(invest[2]) + invest[3]) + marg

    # Investkosten

    results.Wert["annualisierte Investkosten"] = (
        sum(invest[0]) + invest[1] + sum(invest[2]) + invest[3]
    )

    results.Wert["annualisierte Investkosten elektrisches Netz"] = sum(invest[0])

    results.Wert["annualisierte Investkosten PV-Anlagen"] = invest[3]

    results.Wert["annualisierte Investkosten Batteriespeicher"] = invest[2][0]

    results.Wert["annualisierte Investkosten Wärmespeicher"] = invest[2][1]

    results.Wert["annualisierte Investkosten Biogasspeicher"] = invest[2][2]

    results.Wert["annualisierte Investkosten diverser Link-Komponenten"] = invest[1]

    # marginale Kosten

    results.Wert["annualisierte marginale Kosten"] = marg

    results.Wert["Erträge aus Trocknungsanlage"] = network.links_t.p0["TA"].mul(
        network.snapshot_weightings.objective, axis=0
    ).sum() * (network.links.loc["TA"].marginal_cost)

    results.Wert["Erträge aus Netzeinspeisung"] = network.links_t.p0["NA_Sp"].mul(
        network.snapshot_weightings.objective, axis=0
    ).sum() * (network.links.loc["NA_Sp"].marginal_cost)

    results.Wert["Kosten aus Netzbezug"] = network.generators_t.p["NeAn"].mul(
        network.snapshot_weightings.objective, axis=0
    ).sum() * (network.generators.loc["NeAn"].marginal_cost)

    results.Wert["Kosten aus Betrieb der BHKWs (inklusive Biogas)"] = (
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

    results.Wert["abs. Netzausbau"] = calc_network_expansion(network)[0].sum()

    ext_lines = network.lines[network.lines.s_nom_extendable]
    if calc_network_expansion(network)[0].sum() > 0:
        results.Wert["rel. Netzausbau"] = (
            calc_network_expansion(network)[0].sum()
        ) / ext_lines.s_nom.sum()
    else:
        results.Wert["rel. Netzausbau"] = 0

    results.Wert["Ausbau PV-Anlagen"] = (
        (network.generators.p_nom_opt - network.generators.p_nom_min)[
            network.generators.p_nom_extendable
        ]
        .groupby(network.generators.carrier)
        .sum()
        .sum()
    )

    results.Wert["Ausbau Batteriespeicher"] = (
        (network.storage_units.p_nom_opt - network.storage_units.p_nom_min)[
            network.storage_units.p_nom_extendable
        ]
        .groupby(network.storage_units.carrier)
        .sum()
        .sum()
    )

    results.Wert["Ausbau Wärmespeicher"] = (
        network.stores.e_nom_opt - network.stores.e_nom_min
    )[network.stores.index == "WSp"].sum()
    results.Einheit["Ausbau Wärmespeicher"] = "MWh"

    results.Wert["Ausbau Gasspeicher"] = (
        network.stores.e_nom_opt - network.stores.e_nom_min
    )[network.stores.index == "GSp"].sum()

    # Systemversorgung

    results.Wert["elektrische Last IES"] = (
        network.loads_t.p[network.loads[network.loads.carrier == "AC"].index]
        .sum()
        .sum()
        - network.loads_t.p["EV_el"].sum()
    )

    results.Wert["elektrischer Eigenverbrauch BGA"] = network.loads_t.p["EV_el"].sum()

    results.Wert["Wärmelast (Wärmenetz)"] = network.loads_t.p["WL"].sum().sum()

    results.Wert["Eigenverbrauch"] = network.loads_t.p["EV_W"].sum()

    results.Wert["Erzeugung aus PV-Anlagen"] = (
        network.generators_t.p[
            network.generators[network.generators.carrier == "PV"].index
        ]
        .sum()
        .sum()
    )

    results.Wert["Erzeugung durch BHKW - Strom"] = abs(
        network.links_t.p1[network.links[network.links.carrier == "KWK_AC"].index]
        .sum()
        .sum()
    )

    results.Wert["Erzeugung durch BHKW - Wärme"] = abs(
        network.links_t.p1[network.links[network.links.carrier == "KWK_heat"].index]
        .sum()
        .sum()
    )

    results.Wert["Erzeugung durch Spitzenlastkessel"] = network.generators_t.p[
        "SpK"
    ].sum()

    results.Wert["Last der Trocknungsanlage"] = network.links_t.p0["TA"].sum()

    results.Wert["restliche Abwärme"] = network.links_t.p0["Abw"].sum()

    results.Wert["Netzbezug"] = network.generators_t.p["NeAn"].sum()

    results.Wert["Netzeinspeisung"] = network.links_t.p0["NA_Sp"].sum()

    results.Wert["Biogaserzeugung"] = (
        network.generators_t.p["BGA1"].sum() + network.generators_t.p["BGA2"].sum()
    )

    return results
