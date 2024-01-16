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
            (ext_links.p_nom_opt - ext_links.p_nom) * ext_links.capital_cost
        ).sum()

    # Batteriespeicher, Wärmespeicher, Biogasspeicher
    sto_costs = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    ext_storage = network.storage_units[network.storage_units.p_nom_extendable]
    ext_store = network.stores[network.stores.e_nom_extendable]

    if not ext_storage.empty:
        Sto = ext_storage[ext_storage.index == "BSp"]
        sto_costs[0] = ((Sto.p_nom_opt - Sto.p_nom_min) * Sto.capital_cost).sum()
        Sto1 = ext_storage[ext_storage.index == "BSp_KN1"]
        sto_costs[1] = ((Sto1.p_nom_opt - Sto1.p_nom_min) * Sto1.capital_cost).sum()
        Sto2 = ext_storage[ext_storage.index == "BSp_KN2"]
        sto_costs[2] = ((Sto2.p_nom_opt - Sto2.p_nom_min) * Sto2.capital_cost).sum()
        Sto3 = ext_storage[ext_storage.index == "BSp_KN3"]
        sto_costs[3] = ((Sto3.p_nom_opt - Sto3.p_nom_min) * Sto3.capital_cost).sum()
        Sto4 = ext_storage[ext_storage.index == "BSp_KN4"]
        sto_costs[4] = ((Sto4.p_nom_opt - Sto4.p_nom_min) * Sto4.capital_cost).sum()
        Sto5 = ext_storage[ext_storage.index == "BSp_KN5"]
        sto_costs[5] = ((Sto5.p_nom_opt - Sto5.p_nom_min) * Sto5.capital_cost).sum()
        Sto6 = ext_storage[ext_storage.index == "BSp_KN6"]
        sto_costs[6] = ((Sto6.p_nom_opt - Sto6.p_nom_min) * Sto6.capital_cost).sum()
        
    if not ext_store.empty:
        heat = ext_store[ext_store.index == "WSp"]
        sto_costs[7] = ((heat.e_nom_opt - heat.e_nom_min) * heat.capital_cost).sum()
        gas1 = ext_store[ext_store.index == "GSp1"]
        sto_costs[8] = ((gas1.e_nom_opt - gas1.e_nom_min) * gas1.capital_cost).sum()
        gas2 = ext_store[ext_store.index == "GSp2"]
        sto_costs[9] = ((gas2.e_nom_opt - gas2.e_nom_min) * gas2.capital_cost).sum()

    # Erzeugungseinheiten
    gen_costs = [0,0,0,0]
    
    ext_gen = network.generators[network.generators.p_nom_extendable]

    if not ext_gen.empty:
        BGA1 = ext_gen[ext_gen.index == "BGA1"]
        gen_costs[0] = ((BGA1.p_nom_opt - BGA1.p_nom_min) * BGA1.capital_cost).sum()
        BGA2 = ext_gen[ext_gen.index == "BGA2"]
        gen_costs[1] = ((BGA2.p_nom_opt - BGA2.p_nom_min) * BGA2.capital_cost).sum()
        PV = ext_gen[ext_gen.carrier == "PV"]
        gen_costs[2] = ((PV.p_nom_opt - PV.p_nom_min) * PV.capital_cost).sum()
        Wind = ext_gen[ext_gen.carrier == "Wind"]
        gen_costs[3] = ((Wind.p_nom_opt - Wind.p_nom_min) * Wind.capital_cost).sum()
    else:
        gen_costs = [0,0,0,0]

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
        columns=["unit", "value"],
        index=[
            "annualisierte Systemkosten",
            "annualisierte Investkosten",
            "annualisierte marginale Kosten",
            "Investkosten: ",
            "annualisierte Investkosten elektrisches Netz",
            "annualisierte Investkosten BGA1",
            "annualisierte Investkosten BGA2",
            "annualisierte Investkosten PV-Anlagen",
            "annualisierte Investkosten WK-Anlagen",            
            "annualisierte Investkosten Batteriespeicher",
            "annualisierte Investkosten Wärmespeicher",
            "annualisierte Investkosten Biogasspeicher 1",
            "annualisierte Investkosten Biogasspeicher 2",
            "annualisierte Investkosten diverser Link-Komponenten",  # Links Wärmespeicher, Links Abwärme und Netzanschluss
            "Ausbau: ",
            "rel. Netzausbau",
            "abs. Netzausbau",
            "Ausbau FW-Links",
            "Ausbau BGA1",
            "Ausbau BGA2",
            "Ausbau PV-Anlagen",
            "Ausbau WK-Anlagen",
            "Ausbau Batteriespeicher",
            "Ausbau Wärmespeicher",
            "Ausbau Gasspeicher 1",
            "Ausbau Gasspeicher 2",
            "Betriebskosten: ",
            "Erträge aus Trocknungsanlage",
            "Erträge aus Netzeinspeisung BGA",
            "Erträge aus Netzeinspeisung PV",
            "Erträge aus Netzeinspeisung WKA",
            "Kosten aus Netzbezug",
            "Kosten aus Betrieb der BHKWs (inklusive Biogas)",
            "Kosten aus Betrieb des SpLK",
            "Betrieb: ",
            "Biogaserzeugung",
            "elektrischer Eigenverbrauch BGA",
            "elektrische Last IES",
            "Erzeugung durch BHKW - Strom",
            "Netzeinspeisung BGA",
            "Erzeugung aus PV-Anlagen",
            "Netzeinspeisung PV",
            "Erzeugung aus WK-Anlagen",
            "Netzeinspeisung Wind",
            "Netzbezug",
            "Wärmelast (Wärmenetz)",
            "Eigenverbrauch",
            "Last der Trocknungsanlage",
            "restliche Abwärme",
            "Erzeugung durch BHKW - Wärme",
            "Erzeugung durch SpLK",
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
    results.unit[results.index.str.contains("verbrauch")] = "MWh"
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
        sum(invest[0]) + invest[1] + sum(invest[2]) + sum(invest[3])
    )

#

    results.value["annualisierte Investkosten elektrisches Netz"] = sum(invest[0])

    results.value["annualisierte Investkosten BGA1"] = invest[3][0]
        
    results.value["annualisierte Investkosten BGA2"] = invest[3][1]
    
    results.value["annualisierte Investkosten PV-Anlagen"] = invest[3][2]
    
    results.value["annualisierte Investkosten WK-Anlagen"] = invest[3][3]

    results.value["annualisierte Investkosten Batteriespeicher"] = sum(invest[2]) - (invest[2][7] + invest[2][8] + invest[2][9])

    results.value["annualisierte Investkosten Wärmespeicher"] = invest[2][7]

    results.value["annualisierte Investkosten Biogasspeicher 1"] = invest[2][8]
    
    results.value["annualisierte Investkosten Biogasspeicher 2"] = invest[2][9]

    results.value["annualisierte Investkosten diverser Link-Komponenten"] = invest[1]

    # marginale Kosten

    results.value["annualisierte marginale Kosten"] = calc_marginal_cost(network)

    results.value["Erträge aus Trocknungsanlage"] = network.links_t.p0["TA"].mul(
        network.snapshot_weightings.objective, axis=0
    ).sum() * (network.links.loc["TA"].marginal_cost)

    results.value["Erträge aus Netzeinspeisung BGA"] = network.links_t.p0["NA_Sp"].mul(
        network.snapshot_weightings.objective, axis=0
    ).sum() * (network.links.loc["NA_Sp"].marginal_cost)

    results.value["Erträge aus Netzeinspeisung PV"] = (network.links_t.p0["NA_Sp1"].mul(network.snapshot_weightings.objective, axis=0).sum() 
                                                       + network.links_t.p0["NA_Sp2"].mul(network.snapshot_weightings.objective, axis=0).sum()
                                                       + network.links_t.p0["NA_Sp3"].mul(network.snapshot_weightings.objective, axis=0).sum()
                                                       + network.links_t.p0["NA_Sp4"].mul(network.snapshot_weightings.objective, axis=0).sum()
                                                       + network.links_t.p0["NA_Sp5"].mul(network.snapshot_weightings.objective, axis=0).sum()
                                                       + network.links_t.p0["NA_Sp6"].mul(network.snapshot_weightings.objective, axis=0).sum()) * (network.links.loc["NA_Sp1"].marginal_cost)

    results.value["Erträge aus Netzeinspeisung WKA"] = network.links_t.p0["NA_Wind"].mul(
        network.snapshot_weightings.objective, axis=0
    ).sum() * (network.links.loc["NA_Wind"].marginal_cost)

    results.value["Kosten aus Netzbezug"] = network.generators_t.p["NeAn"].mul(
        network.snapshot_weightings.objective, axis=0
    ).sum() * (network.generators.loc["NeAn"].marginal_cost)
    
    results.value["Kosten aus Betrieb des SpLK"] = network.generators_t.p["SpK"].mul(
        network.snapshot_weightings.objective, axis=0
    ).sum() * (network.generators.loc["SpK"].marginal_cost)

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

    results.value["abs. Netzausbau"] = calc_network_expansion(network)[0].sum()

    ext_lines = network.lines[network.lines.s_nom_extendable]
    if calc_network_expansion(network)[0].sum() > 0:
        results.value["rel. Netzausbau"] = (
            calc_network_expansion(network)[0].sum()
        ) / ext_lines.s_nom.sum()
    else:
        results.value["rel. Netzausbau"] = 0

    results.value["Ausbau FW-Links"] = ((network.links.p_nom_opt - network.links.p_nom)[network.links.index.str.startswith("AT")].sum().sum() 
                                        + (network.links.p_nom_opt - network.links.p_nom)[network.links.index.str.startswith("HT")].sum().sum()
   )
    
    results.value["Ausbau PV-Anlagen"] = ((network.generators.p_nom_opt - network.generators.p_nom_min)[network.generators.carrier == "PV"]
        .sum()
        .sum()
    )

    results.value["Ausbau WK-Anlagen"] = ((network.generators.p_nom_opt - network.generators.p_nom_min)[network.generators.carrier == "Wind"]
        .sum()
        .sum()
    )    

    #        .groupby(network.generators.carrier)  
    results.value["Ausbau BGA1"] = ((network.generators.p_nom_opt - network.generators.p_nom_min)[network.generators.index == "BGA1"]
        .sum()
        .sum()
    )
    
    results.value["Ausbau BGA2"] = ((network.generators.p_nom_opt - network.generators.p_nom_min)[network.generators.index == "BGA2"]
        .sum()
        .sum()
    )

    results.value["Ausbau Batteriespeicher"] = (
        (network.storage_units.p_nom_opt - network.storage_units.p_nom_min)[
            network.storage_units.p_nom_extendable
        ]
        .groupby(network.storage_units.carrier)
        .sum()
        .sum()
    )

    results.value["Ausbau Wärmespeicher"] = (
        network.stores.e_nom_opt - network.stores.e_nom
    )[network.stores.index == "WSp"].sum()
    results.unit["Ausbau Wärmespeicher"] = "MWh"

    results.value["Ausbau Gasspeicher 1"] = (
        network.stores.e_nom_opt - network.stores.e_nom_min
    )[network.stores.index == "GSp1"].sum()

    results.value["Ausbau Gasspeicher 2"] = (
        network.stores.e_nom_opt - network.stores.e_nom_min
    )[network.stores.index == "GSp2"].sum()
    
    # Systemversorgung

    results.value["elektrische Last IES"] = (
        network.loads_t.p[network.loads[network.loads.carrier == "AC"].index]
        .sum()
        .sum()
        - network.loads_t.p["EV_el"].sum()
    )

    results.value["elektrischer Eigenverbrauch BGA"] = network.loads_t.p["EV_el"].sum()

    results.value["Wärmelast (Wärmenetz)"] = network.loads_t.p["WL"].sum().sum()
    #network.loads_t.p["WL"].sum().sum()
    #-network.links_t.p1["HT_1"].sum().sum()-network.links_t.p1["HT_72"].sum().sum()
    
    results.value["Eigenverbrauch"] = network.loads_t.p["EV_W"].sum()

    results.value["Erzeugung aus PV-Anlagen"] = (
        network.generators_t.p[
            network.generators[network.generators.carrier == "PV"].index
        ]
        .sum()
        .sum()
    )

    results.value["Erzeugung aus WK-Anlagen"] = (
        network.generators_t.p[
            network.generators[network.generators.carrier == "Wind"].index
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

    results.value["Erzeugung durch SpLK"] = network.generators_t.p[
        "SpK"
    ].sum()

    results.value["Last der Trocknungsanlage"] = network.links_t.p0["TA"].sum()

    results.value["restliche Abwärme"] = network.links_t.p0["Abw"].sum()

    results.value["Netzbezug"] = network.generators_t.p["NeAn"].sum()

    results.value["Netzeinspeisung BGA"] = network.links_t.p0["NA_Sp"].sum()

    results.value["Netzeinspeisung PV"] = network.links_t.p0["NA_Sp1"].sum() + network.links_t.p0["NA_Sp2"].sum() + network.links_t.p0["NA_Sp3"].sum() + network.links_t.p0["NA_Sp4"].sum() + network.links_t.p0["NA_Sp5"].sum() + network.links_t.p0["NA_Sp6"].sum()

    results.value["Netzeinspeisung Wind"] = network.links_t.p0["NA_Wind"].sum()

    results.value["Biogaserzeugung"] = (
        network.generators_t.p["BGA1"].sum() + network.generators_t.p["BGA2"].sum()
    )

    return results
