"""Executa o módulo empírico (Taylor, Phillips, SVAR e LP) e imprime um resumo."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from macrodata.empirical import run  # noqa: E402

if __name__ == "__main__":
    out = run()
    print(out["diag"].to_string(index=False))
    print("\nTaylor (longo prazo):")
    print(out["taylor"]["table"][out["taylor"]["table"]["variavel"].str.contains("longo")].to_string(index=False))
    print("\nCross-country:")
    print(out["cc"].to_string(index=False))
