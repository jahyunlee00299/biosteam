#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Revised D-Tagatose Process Diagrams (Updated 2026-02-01)

User Feedback Applied:
1. NAD+: 0.5 mol → 1.0 mol (1 mM per 1000L)
2. NADP+: 0.6 mol → 0.1 mol (0.1 mM per 1000L)
3. E. coli catalyst: 12.5 kg → 20 kg dry ($50/kg DCW)
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
        eco [label="E.coli Catalyst\n20 kg dry\n$1,000/batch", color="#B0E0E6"];
        acid [label="Acid (pH Buffer)\nFor pH 8.0\nSimple method", color="#90EE90"];
        nad [label="NAD+ Cofactor\n1.0 mol\n$710/batch", color="#FFB6C1"];
        ndp [label="NADP+ Cofactor\n0.1 mol\n$500/batch", color="#FFB6C1"];
        air [label="Compressed Air\n500 kg\n21pct O2", color="#FFE4B5"];
    }

    subgraph cluster_r1 {
        label="Bioreactor (1000L, 30hr, 25C)";
        style=filled;
        color=lightyellow;

        s1 [label="Stage 1: Anaerobic (16h)\nGalactose to Galactitol\nCO2 RELEASED\nOTR: 0", color="#FFFFE0"];
        s2 [label="Stage 2: Aerobic (8h)\nGalactitol to Tagatose\nOTR: 19.1 mmol/(Lh)", color="#FFD700"];
    }

    cent [label="Centrifuge (S1)\n98pct recovery", color="#FFFFE0"];
    decolor [label="Decolorization (D1)\nActivated Carbon", color="#FFFFE0"];
    desalt [label="Desalination (DS1)\nIon Exchange (Amberlite IRC120)", color="#FFFFE0"];
    dry [label="Fluid Bed Dryer (FD1)\nDirect Drying\n98pct conversion path", color="#FFFFE0"];

    prod [label="FINAL PRODUCT\nD-Tagatose\n~110 kg/batch\n>95pct purity\nDirect Dry Powder", shape=ellipse, color="#90EE90"];
    co2 [label="CO2 Gas\n(Stage 1)", shape=ellipse, color="#D3D3D3"];

    econ [label="DIRECT DRYING ECONOMICS (98% conversion, 30h batch):\nNAD+: $710/mol | NADP+: $5,000/mol | E. coli: $50/kg DCW\nCAPEX: $520K (removed evaporator & crystallizer, added FBD)\nOPEX: Desalting $1,409/yr + Drying Energy $350/yr\nAnnual Production: ~27,500 kg (250 batches/yr)\nBreakeven: ~$32/kg | Market: $8-12/kg",
          shape=note, color="#FFFACD"];

    gal->s1; for->s1; eco->s1; nad->s1; acid->s1;
    ndp->s2; air->s2;
    s1->s2 [label="Galactitol"];
    s1->co2 [label="CO2"];
    s2->cent [label="110kg product"];
    cent->decolor [label="107.8kg"];
    decolor->desalt [label="105.6kg"];
    desalt->dry [label="105kg"];
    dry->prod [label="~104.5kg"];
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

            eco [label="E.coli Catalyst\n20 kg dry\n$1,000/batch", color="#B0E0E6"];
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
        label="STAGE 2: BIOREACTION (1000L, 30hr, 25C)";
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
        label="STAGE 3: PURIFICATION & DRYING";
        style=filled;
        color="#F0F8E0";
        fontsize=12;

        cent [label="Centrifuge (S1)\n98 percent recovery", color="#FFFFE0"];
        decolor [label="Decolorization (D1)\nActivated Carbon\n95 percent removal", color="#FFFFE0"];
        desalt [label="Desalination (DS1)\nIon Exchange (Amberlite)\n90 percent Na+ removal", color="#FFFFE0"];
        dry [label="Fluid Bed Dryer (FD1)\nDirect Drying\nYield: ~104.5 kg/batch", color="#FFFFE0"];
    }

    subgraph cluster_output {
        label="STAGE 4: OUTPUT";
        style=filled;
        color="#F0E0F0";
        fontsize=12;

        prod [label="Final Product\nD-Tagatose\n~110 kg/batch\n>95 percent purity\nDirect Dry Powder", shape=ellipse, color="#90EE90"];
        co2 [label="CO2 Gas\n61 mol (Stage 1)", shape=ellipse, color="#D3D3D3"];
    }

    subgraph cluster_econ {
        label="ECONOMIC IMPACT (DIRECT DRYING)";
        style=filled;
        color="#FFE4F0";
        fontsize=10;

        econ [label=
            "DIRECT DRYING ECONOMICS (98% conversion, 30h batch):\nNAD+: $710/mol | NADP+: $5,000/mol | E. coli: $50/kg DCW\n\nCAPEX Optimization:\n  Removed: Crystallization ($50K) + Evaporator ($40K)\n  Added: Fluid Bed Dryer ($80K)\n  Net CAPEX Change: -$10K -> ~$520K total\n\nOPEX Changes:\n  Desalting (Amberlite IRC120): +$1,409/yr\n  Drying Energy (FBD): +$350/yr\n  Annual Production: 27,500 kg (250 batches/yr)\n\nBreakeven: ~$32/kg | Market: $8-12/kg",
            shape=note, color="#FFCCDD", fontsize=7];
    }

    gal->s1; for->s1; eco->s1; nad->s1; acid->s1; ndp->s2; air->s2;
    s1->s2 [label="Galactitol"];
    s1->co2; s2->cent;
    cent->decolor; decolor->desalt; desalt->dry; dry->prod;
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
   E. coli: 12.5 → 20 kg dry, $25 → $50/kg DCW
   YPD: Removed (process simplification)
   pH: Acid buffering method (simplified)
   CO2: Stage 1 (confirmed)

FINAL ECONOMICS (E. coli $50/kg + Tufvesson 2011 verified prices):
   OPEX: $1,054,150/year
   Cost/kg: $31.68 (without cofactor recovery)
   Cost/kg: $24.51 (with 80% NAD+ recovery)
   Cost/kg: $20.87 (with 80% NAD+ & NADP+ recovery)
   Breakeven (w/ CAPEX): $31.68/kg
   Market price: $8-12/kg

See D_TAGATOSE_PROCESS_FINAL.md for complete details.
""")

print("="*100)
print("[DONE]")
print("="*100)
