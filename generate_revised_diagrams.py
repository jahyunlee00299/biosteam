#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revised D-Tagatose Process Diagrams (Updated 2026-02-01)

User Feedback Applied:
1. NAD+: 0.5 mol → 1.0 mol (1 mM per 1000L)
2. NADP+: 0.6 mol → 0.1 mol (0.1 mM per 1000L)
3. E. coli catalyst: 12.5 kg → 25 kg
4. YPD Media: 1000 L → REMOVED
5. pH: Adjusted with acid (simpler method)
6. CO2: Stage 1 (confirmed as correct)

Updated cost structure included
"""

import subprocess
import os

print("="*100)
print("GENERATING REVISED PROCESS DIAGRAMS")
print("Applied User Feedback (2026-02-01)")
print("="*100)

# ========== VERSION 1: REVISED SIMPLE DIAGRAM ==========
dot_simple_revised = r"""
digraph tagatose_revised {
    rankdir=LR;
    node [shape=box, style="rounded,filled", fontname="Arial"];

    subgraph cluster_feed {
        label="Feed Inputs (REVISED per 1000L batch)";
        style=filled;
        color=lightblue;

        gal [label="D-Galactose\n110 kg\n$308/batch", color="#87CEEB"];
        for [label="Sodium Formate\n44 kg\n$79/batch", color="#87CEEB"];
        eco [label="E.coli Catalyst\n25 kg dry (2x)\n$88/batch (2x)", color="#B0E0E6"];
        acid [label="Acid (pH Buffer)\nFor pH 8.0\nSimple method", color="#90EE90"];
        nad [label="NAD+ Cofactor\n1.0 mol\n$710/batch", color="#FFB6C1"];
        ndp [label="NADP+ Cofactor\n0.1 mol\n$500/batch", color="#FFB6C1"];
        air [label="Compressed Air\n500 kg\n21pct O2", color="#FFE4B5"];
    }

    subgraph cluster_r1 {
        label="Bioreactor (1000L, 24hr, 25C)";
        style=filled;
        color=lightyellow;

        s1 [label="Stage 1: Anaerobic (16h)\nGalactose to Galactitol\nCO2 RELEASED\nOTR: 0", color="#FFFFE0"];
        s2 [label="Stage 2: Aerobic (8h)\nGalactitol to Tagatose\nOTR: 19.1 mmol/(Lh)", color="#FFD700"];
    }

    cent [label="Centrifuge (S1)\n98pct recovery", color="#FFFFE0"];
    decolor [label="Decolorization (D1)\nActivated Carbon", color="#FFFFE0"];
    desalt [label="Desalination (DS1)\nIon Exchange", color="#FFFFE0"];
    conc [label="Concentration (T1)\nVacuum Evaporation", color="#FFFFE0"];

    prod [label="FINAL PRODUCT\nD-Tagatose\n104.5 kg/batch\n99.2pct purity", shape=ellipse, color="#90EE90"];
    co2 [label="CO2 Gas\n(Stage 1)", shape=ellipse, color="#D3D3D3"];

    econ [label="UPDATED ECONOMICS (Tufvesson 2011):\nNAD+: $710/mol (was $150)\nNADP+: $5,000/mol (was $200)\nCofactor cost: $378,125/yr\nTotal OPEX: $1,074,225/yr\nCost/kg: $31.25\nWith 80pct recovery: $22.45/kg\nMarket: $8-12/kg",
          shape=note, color="#FFFACD"];

    gal->s1; for->s1; eco->s1; nad->s1; acid->s1;
    ndp->s2; air->s2;
    s1->s2 [label="Galactitol"];
    s1->co2 [label="CO2"];
    s2->cent [label="110kg product"];
    cent->decolor [label="107.8kg"];
    decolor->desalt [label="105.6kg"];
    desalt->conc [label="105kg"];
    conc->prod [label="104.5kg"];
}
"""

# ========== VERSION 2: REVISED CLUSTER DIAGRAM ==========
dot_cluster_revised = r"""
digraph tagatose_cluster_revised {
    rankdir=TB;
    fontname="Arial";
    node [shape=box, style="rounded,filled", fontname="Arial"];

    subgraph cluster_input {
        label="STAGE 1: INPUT (REVISED)";
        style=filled;
        color="#E0F0FF";
        fontsize=12;

        subgraph cluster_chem {
            label="Chemical Feeds";
            style=filled;
            color="#D0E8FF";

            gal [label="D-Galactose\n110 kg\n$308/batch", color="#87CEEB"];
            for [label="Sodium Formate\n44 kg\n$79/batch", color="#87CEEB"];
        }

        subgraph cluster_bio {
            label="Biological & Buffers";
            style=filled;
            color="#D0E8FF";

            eco [label="E.coli Catalyst\n25 kg dry (2x)\n$88/batch (2x)", color="#B0E0E6"];
            acid [label="Acid Buffer\nFor pH 8.0\nReplaces YPD\nSimpler method", color="#90EE90"];
        }

        subgraph cluster_cofactor {
            label="Cofactors";
            style=filled;
            color="#D0E8FF";

            nad [label="NAD+\n1.0 mol\n$710/batch", color="#FFB6C1"];
            ndp [label="NADP+\n0.1 mol\n$500/batch", color="#FFB6C1"];
        }

        air [label="Compressed Air\n500 kg\n21 percent O2", color="#FFE4B5"];
    }

    subgraph cluster_reaction {
        label="STAGE 2: BIOREACTION (1000L, 24hr, 25C)";
        style=filled;
        color="#FFFACD";
        fontsize=12;

        subgraph cluster_anaerobic {
            label="Anaerobic Phase (16h)";
            style=filled;
            color="#FFE4CC";

            s1 [label="Stage 1: ANAEROBIC\nGalactose to Galactitol\nCO2 RELEASE (61 mol)\nOTR: 0 mmol/(L*h)\nConversion: 99.5 percent", color="#FFFFE0", fontsize=8];
        }

        subgraph cluster_aerobic {
            label="Aerobic Phase (8h)";
            style=filled;
            color="#FFD699";

            s2 [label="Stage 2: AEROBIC\nGalactitol to Tagatose\nO2 consumption: 152.8 mol\nOTR: 19.1 mmol/(L*h)\nConversion: 98 percent", color="#FFD700", fontsize=8];
        }
    }

    subgraph cluster_purification {
        label="STAGE 3: PURIFICATION";
        style=filled;
        color="#F0F8E0";
        fontsize=12;

        cent [label="Centrifuge (S1)\n98 percent recovery", color="#FFFFE0"];
        decolor [label="Decolorization (D1)\nActivated Carbon\n95 percent removal", color="#FFFFE0"];
        desalt [label="Desalination (DS1)\nIon Exchange\n90 percent Na+ removal", color="#FFFFE0"];
        conc [label="Concentration (T1)\nVacuum Evaporation\n104.5 kg yield", color="#FFFFE0"];
    }

    subgraph cluster_output {
        label="STAGE 4: OUTPUT";
        style=filled;
        color="#F0E0F0";
        fontsize=12;

        prod [label="Final Product\nD-Tagatose\n104.5 kg/batch\n99.2 percent purity", shape=ellipse, color="#90EE90"];
        co2 [label="CO2 Gas\n61 mol (Stage 1)", shape=ellipse, color="#D3D3D3"];
    }

    subgraph cluster_econ {
        label="ECONOMIC IMPACT (REVISED)";
        style=filled;
        color="#FFE4F0";
        fontsize=10;

        econ [label=
            "COFACTOR PRICE UPDATE (Tufvesson 2011):\nNAD+: $710/mol (was $150)\nNADP+: $5,000/mol (was $200)\n\nCofactor Annual: $378,125/yr (35.2pct OPEX)\nTotal OPEX: $1,074,225/yr\nCost/kg: $31.25 (no recovery)\nCost/kg: $22.45 (80pct dual recovery)\nMarket: $8-12/kg\n\nCRITICAL: Cofactor regeneration MANDATORY\nNAD+ recovery saves $177,500/yr\nNADP+ recovery saves $125,000/yr",
            shape=note, color="#FFCCDD", fontsize=7];
    }

    gal->s1; for->s1; eco->s1; nad->s1; acid->s1; ndp->s2; air->s2;
    s1->s2 [label="Galactitol"];
    s1->co2; s2->cent;
    cent->decolor; decolor->desalt; desalt->conc; conc->prod;
}
"""

# Generate simple and cluster diagrams only
diagrams = [
    ('tagatose_revised_simple.dot', dot_simple_revised, 'tagatose_revised_simple.svg'),
    ('tagatose_revised_cluster.dot', dot_cluster_revised, 'tagatose_revised_cluster.svg'),
]

for dot_file, dot_content, svg_file in diagrams:
    print(f"\n[Creating] {dot_file}...")
    with open(dot_file, 'w') as f:
        f.write(dot_content)

    print(f"[Rendering] {svg_file}...")
    try:
        result = subprocess.run(['dot', '-Tsvg', dot_file, '-o', svg_file],
                              capture_output=True, text=True, timeout=15)
        if result.returncode == 0 and os.path.exists(svg_file):
            size = os.path.getsize(svg_file) / 1024
            print(f"[OK] {svg_file} ({size:.1f} KB)")
        else:
            print(f"[ERROR] {result.stderr}")
    except Exception as e:
        print(f"[ERROR] {e}")

print("\n" + "="*100)
print("[SUMMARY]")
print("="*100)

print("""
PROCESS DIAGRAMS GENERATED:

1. tagatose_revised_simple.svg
   └─ Overview for presentations (non-technical)

2. tagatose_revised_cluster.svg
   └─ Detailed technical analysis (hierarchical)

KEY CHANGES APPLIED:
   NAD+: 0.5 → 1.0 mol (1 mM per 1000L)
   NADP+: 0.6 → 0.1 mol (0.1 mM per 1000L)
   E. coli: 12.5 → 25 kg (2x increase)
   YPD: Removed (process simplification)
   pH: Acid buffering method (simplified)
   CO2: Stage 1 (confirmed)

FINAL ECONOMICS (Tufvesson 2011 verified prices):
   OPEX: $1,074,225/year
   Cost/kg: $31.25 (without cofactor recovery)
   Cost/kg: $26.09 (with 80% NAD+ recovery)
   Cost/kg: $22.45 (with 80% NAD+ & NADP+ recovery)
   Market price: $8-12/kg

See D_TAGATOSE_PROCESS_FINAL.md for complete details.
""")

print("="*100)
print("[DONE]")
print("="*100)
