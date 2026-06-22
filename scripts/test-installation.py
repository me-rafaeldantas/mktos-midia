#!/usr/bin/env python3
"""
test-installation.py — Script de teste para validar a estrutura e arquivos criados.
"""

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).parent.parent.resolve()


def test_manifests():
    print("Testando manifestos...")
    plugin_json = REPO_ROOT / "plugin.json"
    gemini_json = REPO_ROOT / "gemini-extension.json"

    assert plugin_json.exists(), "plugin.json não encontrado na raiz!"
    assert gemini_json.exists(), "gemini-extension.json não encontrado na raiz!"

    with open(plugin_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data.get("name") == "mktos-midia", "Nome incorreto no plugin.json!"

    with open(gemini_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data.get("name") == "mktos-midia", "Nome incorreto no gemini-extension.json!"

    print("✓ Manifestos válidos.")


def test_scripts():
    print("Testando scripts novos e executabilidade...")
    configurar_mcp = REPO_ROOT / "scripts" / "configurar-mcp.py"
    install_sh = REPO_ROOT / "install.sh"

    assert configurar_mcp.exists(), "configurar-mcp.py não encontrado!"
    assert install_sh.exists(), "install.sh não encontrado!"

    # Verifica erros de sintaxe compilando o arquivo
    import py_compile
    try:
        py_compile.compile(str(configurar_mcp), doraise=True)
        print("✓ configurar-mcp.py compilado com sucesso (sem erros de sintaxe).")
    except Exception as e:
        print(f"✗ Erro de compilação/sintaxe em configurar-mcp.py: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        test_manifests()
        test_scripts()
        print("\n🎉 TODOS OS TESTES PASSARAM! A estrutura de distribuição e compatibilidade está perfeita.")
    except AssertionError as e:
        print(f"\n✗ TESTE FALHOU: {e}")
        sys.exit(1)
