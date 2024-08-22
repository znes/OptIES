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
This file contains the functions to examine the optimization results.
"""

import pandas as pd
import numpy as np

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
            (ext_lines.s_nom_opt - ext_lines.s_nom_min)
            * ext_lines.capital_cost
        ).sum()

    if not ext_trafos.empty:
        network_costs[0] = (
            network_costs[0]
            + (
                (ext_trafos.s_nom_opt - ext_trafos.s_nom)
                * ext_trafos.capital_cost
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
            (ext_links.p_nom_opt - ext_links.p_nom_min)
            * ext_links.capital_cost
        ).sum()

    # Batteriespeicher, Wärmespeicher, Biogasspeicher
    sto_costs = [0, 0, 0]

    ext_storage = network.storage_units[network.storage_units.p_nom_extendable]
    ext_store = network.stores[network.stores.e_nom_extendable]

    if not ext_storage.empty:
        sto_costs[0] = (
            (ext_storage.p_nom_opt - ext_storage.p_nom_min)
            * ext_storage.capital_cost
        ).sum()

    if not ext_store.empty:
        heat = ext_store[ext_store.index == "WSp"]
        sto_costs[1] = (
            (heat.e_nom_opt - heat.e_nom_min) * heat.capital_cost
        ).sum()
        gas = ext_store[ext_store.index == "GSp"]
        sto_costs[2] = (
            (gas.e_nom_opt - gas.e_nom_min) * gas.capital_cost
        ).sum()

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
    if network.snapshots[1] - network.snapshots[0] == pd.Timedelta(minutes=5):
        res = 12
    elif network.snapshots[1] - network.snapshots[0] == pd.Timedelta(
        minutes=15
    ):
        res = 4
    else:
        res = 1

    gen = (
        network.generators_t.p.groupby(
            np.arange(len(network.snapshots)) // res
        )
        .mean()
        .sum()
        .mul(network.generators.marginal_cost)
        .sum()
    )

    link = (
        abs(network.links_t.p0)
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum(axis=0)
        .mul(network.links.marginal_cost)
        .sum()
    )

    stor = (
        network.storage_units_t.p.groupby(
            np.arange(len(network.snapshots)) // res
        )
        .mean()
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

def battery_usage(network):
    use = (
        network.storage_units_t.p
    ).clip(lower=0).sum().sum() * 1000
    
    return use

def dsm_potential_usage(network):
    pot = (
        network.links[network.links.index.str.contains("dsm")].p_nom
        * network.links_t.p_max_pu[
            network.links[network.links.index.str.contains("dsm")].index
        ].mean()
    ).sum() * 1000
    use = (network.links_t.p0[
            network.links[network.links.index.str.contains("dsm")].index
        ].clip(lower=0)
    ).sum().sum() * 1000

    return pot, use


def emob_potential_usage(network):
    pot = (
        network.links[network.links.index.str.contains("_flex")].p_nom
        * network.links_t.p_max_pu[
            network.links[network.links.index.str.contains("_flex")].index
        ].mean()
    ).sum() * 1000
    use = (
        network.links_t.p0[
            network.links[network.links.index.str.contains("_flex")].index
        ].clip(lower=0)
    ).sum().sum() * 1000

    return pot, use


def calc_ghg_emissions(network):
    if network.snapshots[1] - network.snapshots[0] == pd.Timedelta(minutes=5):
        res = 12
    elif network.snapshots[1] - network.snapshots[0] == pd.Timedelta(
        minutes=15
    ):
        res = 4
    else:
        res = 1

    # Energiemengen in MWh
    
    production_pv = (
        network.generators_t.p[
            network.generators[network.generators.carrier == "PV"].index
        ]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        .sum()
    )

    production_grid = (
        network.generators_t.p["NeAn"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    load_ies = (
        network.loads_t.p_set[
            network.loads[network.loads.carrier == "AC"].index
        ]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        .sum()
        - network.loads_t.p_set["EV_el"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    load_minus_pv_grid = load_ies - production_pv - production_grid

    # spez. Emissionen in g/kWh
    # Quelle für spez. Emissionen von PV und Biomasse:
    # https://www.ipcc.ch/site/assets/uploads/2018/02/ipcc_wg3_ar5_annex-iii.pdf
    # Seite 1335
    # Quelle für spez. Emissionen von Netzbezug (Durchschnittswert aus 2023):
    # https://www.umweltbundesamt.de/themen/co2-emissionen-pro-kilowattstunde-strom-2023
    emissions_sp_pv = 41
    emissions_sp_biomass_AC = 230
    emissions_sp_grid = 380
    emissionen_leitungen = 0

    emissions_abs_pv = production_pv * emissions_sp_pv
    emissions_abs_grid = production_grid * emissions_sp_grid
    emissions_load_minus_pv_grid = load_minus_pv_grid * emissions_sp_biomass_AC

    # abs. emissionen in kg (MWh*(g/kWh) = kg)
    emissions_total = (
        emissions_load_minus_pv_grid + emissions_abs_pv + emissions_abs_grid
    )
    return emissions_total


def calc_autarkiegrad(network):
    pv = network.generators[network.generators.carrier == "PV"]
    pv_gen = network.generators_t.p[pv.index].sum(axis=1)

    loads = network.loads[
        (network.loads.carrier == "AC") & (network.loads.bus != "BGA_AC")
    ]
    network.loads_t.p_set[loads.index]
    sum_loads = network.loads_t.p_set[loads.index].sum(axis=1)

    diff = pv_gen >= sum_loads
    diff.value_counts(True)

    share_of_autarkic_hours = (diff.value_counts()[1] / 8760) * 100

    return share_of_autarkic_hours


def calc_pv_share_of_load(network):
    if network.snapshots[1] - network.snapshots[0] == pd.Timedelta(minutes=5):
        res = 12
    elif network.snapshots[1] - network.snapshots[0] == pd.Timedelta(
        minutes=15
    ):
        res = 4
    else:
        res = 1

    production_pv = (
        network.generators_t.p[
            network.generators[network.generators.carrier == "PV"].index
        ]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        .sum()
    )

    load_ies = (
        network.loads_t.p_set[
            network.loads[network.loads.carrier == "AC"].index
        ]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        .sum()
        - network.loads_t.p_set["EV_el"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    pv_share_of_load = (production_pv / load_ies) * 100

    return pv_share_of_load


def calc_results(network):
    results = pd.DataFrame(
        columns=["Einheit", "Wert"],
        index=[
            "Objective:",
            "Systemkosten: ",
            "annualisierte Systemkosten",
            "annualisierte Investkosten",
            "annualisierte Investkosten elektrisches Netz",
            "annualisierte Investkosten PV-Anlagen",
            "annualisierte Investkosten Batteriespeicher",
            "annualisierte Investkosten Wärmespeicher",
            # "annualisierte Investkosten Biogasspeicher",
            "annualisierte Investkosten diverser Link-Komponenten",  # Links Wärmespeicher, Links Abwärme und Netzanschluss
            "Ausbau: ",
            "rel. Netzausbau",
            "abs. Netzausbau",
            "Ausbau PV-Anlagen",
            "Ausbau Batteriespeicher",
            "Ausbau Wärmespeicher",
            # "Ausbau Gasspeicher",
            "Betriebskosten: ",
            "Erträge aus Trocknungsanlage",
            "Erträge aus Netzeinspeisung",
            "Kosten aus Netzbezug",
            "Kosten aus Betrieb der BHKWs (inklusive Biogas)",
            "Betrieb: ",
            "Biogaserzeugung",
            "elektrischer Eigenverbrauch BGA",
            "elektrische Last IES",
            "- Anschlussnehmer*innen",
            "- Ladesäulen E-Mobilität",
            "Erzeugung aus PV-Anlagen",
            "Erzeugung durch BHKW - Strom",
            "Netzbezug",
            "Netzeinspeisung",
            "Wärmelast (Wärmenetz)",
            "Eigenverbrauch Wärme BGA",
            "Last der Trocknungsanlage",
            "restliche Abwärme",
            "Erzeugung durch BHKW - Wärme",
            "Erzeugung durch Spitzenlastkessel",
            "Treibhausgasemissionen Stromversorgung IES",
            "Anteil der Stunden mit Lastdeckung durch PV",
            "Anteil PV an Stromversorgung IES",
            "Nutzung von Flexibilitäten:",
            "Batteriespeichernutzung (Ausspeicherung)",
            "E-Mobilität - durchschnittliches Potential",
            "E-Mobilität - Nutzung",
            "DSM - durchschnittliches Potential",
            "DSM - Nutzung",
        ],
    )

    results.Einheit[results.index.str.contains("Netzbezug")] = "MWh"
    results.Einheit[results.index.str.contains("Netzeinspeisung")] = "MWh"
    results.Einheit[results.index.str.contains("Kosten")] = "EUR/a"
    results.Einheit[results.index.str.contains("kosten")] = "EUR/a"
    results.Einheit[results.index.str.contains("Erträge")] = "EUR/a"
    results.Einheit[results.index.str.contains("Ausbau")] = "kW"
    results.Einheit[results.index.str.contains("ausbau")] = "kW"
    results.Einheit[results.index.str.contains("Last")] = "MWh"
    results.Einheit[results.index.str.contains("last")] = "MWh"
    results.Einheit[results.index.str.contains("verbrauch")] = "MWh"
    results.Einheit[results.index.str.contains("innen")] = "MWh"
    results.Einheit[results.index.str.contains("E-Mobilität")] = "MWh"
    results.Einheit[results.index.str.contains("restlich")] = "MWh"
    results.Einheit[results.index.str.contains("Erzeugung")] = "MWh"
    results.Einheit[results.index.str.contains("erzeugung")] = "MWh"
    results.Einheit[results.index.str.contains("rel.")] = "p.u."
    results.Einheit[results.index.str.contains("Potential")] = "kW"
    results.Einheit[results.index.str.contains("Nutzung")] = "kWh"
    results.Einheit[results.index.str.contains("nutzung")] = "kWh"
    results.Einheit[
        results.index.str.contains(
            "Treibhausgasemissionen Stromversorgung IES"
        )
    ] = "kg C02e"
    results.Einheit[results.index.str.contains("Anteil")] = "%"
    results.Einheit[results.index.str.contains(":")] = "-"
    results.Wert[results.index.str.contains(":")] = "-"

    results.Wert["Objective"] = network.objective
    results.Einheit["Objective"] = "(€)"

    if network.snapshots[1] - network.snapshots[0] == pd.Timedelta(minutes=5):
        res = 12
    elif network.snapshots[1] - network.snapshots[0] == pd.Timedelta(
        minutes=15
    ):
        res = 4
    else:
        res = 1

    # Systemkosten

    invest = calc_investment_cost(network)

    marg = calc_marginal_cost(network)

    results.Wert["annualisierte Systemkosten"] = (
        sum(invest[0]) + invest[1] + sum(invest[2]) + invest[3]
    ) + marg

    # Investkosten

    results.Wert["annualisierte Investkosten"] = (
        sum(invest[0]) + invest[1] + sum(invest[2]) + invest[3]
    )

    results.Wert["annualisierte Investkosten elektrisches Netz"] = sum(
        invest[0]
    )

    results.Wert["annualisierte Investkosten PV-Anlagen"] = invest[3]

    results.Wert["annualisierte Investkosten Batteriespeicher"] = invest[2][0]

    results.Wert["annualisierte Investkosten Wärmespeicher"] = invest[2][1]

    # results.Wert["annualisierte Investkosten Biogasspeicher"] = invest[2][2]

    results.Wert["annualisierte Investkosten diverser Link-Komponenten"] = (
        invest[1]
    )

    # marginale Kosten

    results.Wert["annualisierte marginale Kosten"] = marg

    results.Wert["Erträge aus Trocknungsanlage"] = network.links_t.p0[
        "TA"
    ].groupby(np.arange(len(network.snapshots)) // res).mean().sum() * (
        network.links.loc["TA"].marginal_cost
    )

    results.Wert["Erträge aus Netzeinspeisung"] = network.links_t.p0[
        "NA_Sp"
    ].groupby(np.arange(len(network.snapshots)) // res).mean().sum() * (
        network.links.loc["NA_Sp"].marginal_cost
    )

    results.Wert["Kosten aus Netzbezug"] = network.generators_t.p[
        "NeAn"
    ].groupby(np.arange(len(network.snapshots)) // res).mean().sum() * (
        network.generators.loc["NeAn"].marginal_cost
    )

    results.Wert["Kosten aus Betrieb der BHKWs (inklusive Biogas)"] = (
        network.generators_t.p["BGA1"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        * (network.generators.loc["BGA1"].marginal_cost)
        + network.generators_t.p["BGA2"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        * (network.generators.loc["BGA2"].marginal_cost)
        + (
            network.links_t.p0[
                network.links[network.links.carrier == "KWK_AC"].index
            ]
            .groupby(np.arange(len(network.snapshots)) // res)
            .mean()
            .sum()
            * (network.links[network.links.carrier == "KWK_AC"].marginal_cost)
        ).sum()
    )

    # Systemausbau

    results.Wert["abs. Netzausbau"] = (
        calc_network_expansion(network)[0].sum() * 1000
    )  # kW

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
    ) * 1000  # kW

    results.Wert["Ausbau Batteriespeicher"] = (
        (network.storage_units.p_nom_opt - network.storage_units.p_nom_min)[
            network.storage_units.p_nom_extendable
        ]
        .groupby(network.storage_units.carrier)
        .sum()
        .sum()
    ) * 1000  # kW

    results.Wert["Ausbau Wärmespeicher"] = (
        network.stores.e_nom_opt - network.stores.e_nom_min
    )[network.stores.index == "WSp"].sum()
    results.Einheit["Ausbau Wärmespeicher"] = "MWh"

    '''results.Wert["Ausbau Gasspeicher"] = (
        network.stores.e_nom_opt - network.stores.e_nom_min
    )[network.stores.index == "GSp"].sum()
    results.Einheit["Ausbau Gasspeicher"] = "MWh"'''

    # Systemversorgung

    results.Wert["elektrische Last IES"] = (
        network.loads_t.p_set[
            network.loads[network.loads.carrier == "AC"].index
        ]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        .sum()
        - network.loads_t.p_set["EV_el"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    results.Wert["- Anschlussnehmer*innen"] = (
        network.loads_t.p_set[
            network.loads[network.loads.carrier == "AC"].index
        ]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        .sum()
        - network.loads_t.p_set["EV_el"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        - network.loads_t.p_set["LS1"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        - network.loads_t.p_set["LS2"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    results.Wert["- Ladesäulen E-Mobilität"] = (
        network.loads_t.p_set["LS1"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        + network.loads_t.p_set["LS2"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    results.Wert["elektrischer Eigenverbrauch BGA"] = (
        network.loads_t.p_set["EV_el"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    results.Wert["Wärmelast (Wärmenetz)"] = (
        network.loads_t.p_set["WL"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        .sum()
    )

    results.Wert["Eigenverbrauch Wärme BGA"] = (
        network.loads_t.p_set["EV_W"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    results.Wert["Erzeugung aus PV-Anlagen"] = (
        network.generators_t.p[
            network.generators[network.generators.carrier == "PV"].index
        ]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        .sum()
    )

    results.Wert["Erzeugung durch BHKW - Strom"] = abs(
        network.links_t.p1[
            network.links[network.links.carrier == "KWK_AC"].index
        ]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        .sum()
    )

    results.Wert["Erzeugung durch BHKW - Wärme"] = abs(
        network.links_t.p1[
            network.links[network.links.carrier == "KWK_heat"].index
        ]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        .sum()
    )

    results.Wert["Erzeugung durch Spitzenlastkessel"] = (
        network.generators_t.p["SpK"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    results.Wert["Last der Trocknungsanlage"] = (
        network.links_t.p0["TA"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    results.Wert["restliche Abwärme"] = (
        network.links_t.p0["Abw"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    results.Wert["Netzbezug"] = (
        network.generators_t.p["NeAn"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    results.Wert["Netzeinspeisung"] = (
        network.links_t.p0["NA_Sp"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    results.Wert["Biogaserzeugung"] = (
        network.generators_t.p["BGA1"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
        + network.generators_t.p["BGA2"]
        .groupby(np.arange(len(network.snapshots)) // res)
        .mean()
        .sum()
    )

    results.Wert["Treibhausgasemissionen Stromversorgung IES"] = (
        calc_ghg_emissions(network)
    )

    results.Wert["Anteil der Stunden mit Lastdeckung durch PV"] = (
        calc_autarkiegrad(network)
    )

    results.Wert["Anteil PV an Stromversorgung IES"] = calc_pv_share_of_load(
        network
    )

    # Nutzung von Flexibilitäten
    
    results.Wert["Batteriespeichernutzung (Ausspeicherung)"] = (
        battery_usage(network))

    results.Wert["DSM - durchschnittliches Potential"] = (
        dsm_potential_usage(network)[0]
    )

    results.Wert["DSM - Nutzung"] = (
        dsm_potential_usage(network)[1]
    )

    results.Wert["E-Mobilität - durchschnittliches Potential"] = (
        emob_potential_usage(network)[0]
    )

    results.Wert["E-Mobilität - Nutzung"] = (
        emob_potential_usage(network)[1]
    )

    return results
