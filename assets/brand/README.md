# Identidade Visual Oficial — Project Nox

Este diretório centraliza os derivados diretos do emblema oficial do Project Nox, garantindo que a organização e o perfil pessoal do fundador compartilhem exatamente o mesmo símbolo.

## Fonte da Verdade

- **Repositório de origem:** `Awerkori/Awerkori`
- **Arquivo original:** `assets/profile/hero.svg`
- **Elemento de referência:** `<image href="data:image/webp;base64,...">` (comentário `Official Emblem WebP (Golden Omega with Alpha inside)`)
- **Formato e dimensões:** WebP lossless com canal alfa (`280 × 280 px`, `82.292` bytes)
- **SHA-256 (`nox-emblem.webp`):** `afa76b5f507bbcf4e2978717badf1863280dc08a38479030ebf9b1671d733555`

## Arquivos Derivados

- `nox-emblem.webp` — Cópia binária extraída sem alterações do emblema oficial.
- `nox-avatar.png` — Avatar 1:1 (`512 × 512 px`) em alta resolução sobre atmosfera cósmica.
- `nox-mark-dark.svg` / `nox-mark-light.svg` — Versões vetoriais 1:1 com o WebP oficial incorporado para tema escuro e claro.
- `../nox-hero-dark.svg` / `../nox-hero-light.svg` — Banners institucionais desktop (`1200 × 300 px`) com o mesmo emblema e sistema de animação orbital.
- `../nox-hero-mobile-dark.svg` / `../nox-hero-mobile-light.svg` — Banners institucionais mobile (`420 × 370 px`) com a mesma identidade e animações.
- `../nox-philosophy-dark.svg` / `../nox-philosophy-light.svg` — Faixa de princípios desktop (`840 × 96 px`).
- `../nox-philosophy-mobile-dark.svg` / `../nox-philosophy-mobile-light.svg` — Faixa de princípios mobile (`380 × 236 px`).

## Dependências e Atualização

Requer **Python >= 3.10** e **Pillow** (`pip install -r scripts/requirements.txt`).

Para re-sincronizar os assets a partir do perfil pessoal:

```bash
python3 scripts/sync-emblem.py
```

Para testar com uma cópia local explícita:

```bash
python3 scripts/sync-emblem.py --source /caminho/para/hero.svg
```

Para atualizar o avatar da organização no GitHub com `nox-avatar.png`:
1. Acesse `https://github.com/organizations/ProjectNox-org/settings/profile`
2. Em **Profile picture**, clique em **Upload new picture** e selecione `assets/brand/nox-avatar.png`.
