# Especificações de Mídia Paga

> **Objetivo:** Referência legível por máquina para validação de criativos pagos, limites de cópia de anúncio, specs de formato e benchmarks de performance por plataforma. Complementa `platform-specs.md` (specs orgânicos) e `industry-profiles.md` (benchmarks por setor).
>
> **Última atualização:** 2026-06-12
>
> **Uso:** Consulte este arquivo ao validar RSAs, briefar criativos de mídia paga, revisar limites de texto, estimar CPM/CPC/CTR ou verificar restrições de política antes de publicar.

---

## Índice

1. [Google Ads](#1-google-ads)
2. [Meta Ads (Facebook & Instagram)](#2-meta-ads-facebook--instagram)
3. [TikTok Ads](#3-tiktok-ads)
4. [LinkedIn Ads](#4-linkedin-ads)
5. [Benchmarks de Performance — Visão Geral](#5-benchmarks-de-performance--visão-geral)
6. [Políticas de Anúncios — Restrições Críticas](#6-políticas-de-anúncios--restrições-críticas)

---

## 1. Google Ads

### Responsive Search Ads (RSA)

| Campo | Limite | Notas |
|---|---|---|
| Headlines | 15 máx / 3 mín | Cada título: máx 30 caracteres |
| Descriptions | 4 máx / 2 mín | Cada descrição: máx 90 caracteres |
| Display URL (path fields) | 2 campos, 15 chars cada | Sem espaços ou caracteres especiais |
| Final URL | obrigatório | Deve corresponder ao conteúdo do anúncio (relevância de destino) |
| Pinning | opcional | Use com parcimônia — reduz variações e prejudica o score de força |

**Força do anúncio:** Google classifica RSAs em Fraco / Razoável / Bom / Excelente. Meta: pelo menos "Bom". Principais drivers: diversidade de headlines, sem repetição, inclusão de palavra-chave principal, CTAs variados.

**Regras de validação automática (publicador-google-ads.py):**
- Máx 15 headlines, cada um ≤ 30 chars
- Máx 4 descriptions, cada um ≤ 90 chars
- Mín 3 headlines e 2 descriptions para criação
- Sem URLs em campos de texto
- Sem uso excessivo de maiúsculas ou pontuação especial

### Display & Performance Max — Assets de Imagem

| Formato | Dimensão | Proporção | Tamanho máx |
|---|---|---|---|
| Paisagem | 1200 × 628 px | 1.91:1 | 5 MB |
| Quadrado | 1200 × 1200 px | 1:1 | 5 MB |
| Portrait | 960 × 1200 px | 4:5 | 5 MB |
| Logo (paisagem) | 1200 × 300 px | 4:1 | 5 MB |
| Logo (quadrado) | 1200 × 1200 px | 1:1 | 5 MB |
| Tamanho mínimo (qualquer) | 600 × 314 px | — | — |

Formatos aceitos: JPG, PNG (sem GIF animado). Texto sobre imagem: máx 20% da área (regra Google Display).

### Assets de Vídeo (YouTube / Performance Max)

| Especificação | Valor |
|---|---|
| Duração mínima | 6 segundos (bumper) / 15s (in-stream) |
| Duração recomendada | 15–30 segundos (in-stream skippable) |
| Resolução mínima | 1280 × 720 px (720p) |
| Resolução recomendada | 1920 × 1080 px (1080p) |
| Proporção | 16:9 (horizontal) ou 9:16 (vertical para Shorts) |
| Formato | MP4, MOV, AVI, WMV |
| Tamanho máximo | 128 GB |
| Frame rate | 30 fps (mín) / 60 fps (recomendado para ação) |

**Hook em 5 segundos:** usuário pode pular após 5s. O ponto mais importante da mensagem deve aparecer nos primeiros 5 segundos.

### Responsive Display Ads (RDA) — Cópia

| Campo | Limite |
|---|---|
| Short headlines | 5 máx, cada ≤ 30 chars |
| Long headline | 1, máx 90 chars |
| Descriptions | 5 máx, cada ≤ 90 chars |
| Business name | obrigatório, máx 25 chars |

### Campanhas — Limites e Boas Práticas

| Parâmetro | Recomendação |
|---|---|
| Ad groups por campanha | 7–10 (máx prático com gestão eficiente) |
| Keywords por ad group | 10–20 (tema único por ad group) |
| RSAs por ad group | 3 (permite testes de variação com rotação equilibrada) |
| Orçamento diário mínimo | R$ 10 (abaixo disso o Google limita aprendizado) |
| Período de aprendizado | 7–14 dias (não alterar estrutura nesse período) |
| Budget guard mktOS | Bloqueia se orçamento diário > 50% do `orcamento_mensal` do perfil |

---

## 2. Meta Ads (Facebook & Instagram)

### Feed — Imagem

| Especificação | Valor |
|---|---|
| Proporção recomendada | 1:1 (quadrado) ou 4:5 (portrait) |
| Resolução mínima | 1080 × 1080 px |
| Formatos | JPG, PNG |
| Tamanho máximo | 30 MB |
| Texto na imagem | Permitido (regra dos 20% removida em 2021, mas imagens sem texto tendem a ter melhor alcance) |

### Feed — Vídeo

| Especificação | Valor |
|---|---|
| Proporção recomendada | 4:5 (portrait) ou 1:1 (quadrado) |
| Resolução mínima | 1080 × 1080 px |
| Duração | 1 segundo – 241 minutos |
| Duração recomendada | 15–30 segundos (feed), até 60s para engajamento profundo |
| Formatos | MP4, MOV |
| Tamanho máximo | 4 GB |
| Frame rate | 24–30 fps |
| Caption automática | Ative sempre — 85% dos vídeos são assistidos sem som |

### Stories e Reels — Vídeo/Imagem

| Especificação | Valor |
|---|---|
| Proporção | 9:16 (vertical, full screen) |
| Resolução mínima | 1080 × 1920 px |
| Duração (Stories — imagem) | 5 segundos |
| Duração (Stories — vídeo) | até 60 segundos |
| Duração (Reels) | até 90 segundos |
| Zona segura | Manter elementos importantes fora de 14% superior e inferior da tela |

### Carrossel

| Especificação | Valor |
|---|---|
| Cards | 2–10 |
| Proporção por card | 1:1 (recomendado para feed) |
| Resolução mínima | 1080 × 1080 px |
| Título por card | máx 40 chars |
| Descrição por card | máx 20 chars |
| URL por card | cada card pode ter link diferente |

### Cópia de Anúncio — Limites

| Campo | Limite | Notas |
|---|---|---|
| Texto principal (body) | 125 chars antes do "ver mais" | Primeiros 125 chars são críticos |
| Headline | 40 chars | Exibido abaixo da imagem/vídeo |
| Descrição | 30 chars | Nem sempre exibida |
| CTA | botão selecionável | Saiba Mais / Comprar / Cadastrar / etc. |

### Segmentação — Limites de Audiência

| Parâmetro | Referência |
|---|---|
| Audiência mínima para veiculação | 1.000 pessoas |
| Audiência mínima recomendada (cold) | 500.000–2M (para otimização de conversão eficiente) |
| Lookalike — mínimo de seed | 100 pessoas (mínimo); 1.000–5.000 (recomendado) |
| Frequência saudável (retargeting) | ≤ 3.5 por 7 dias |
| Frequência de alerta (fadiga) | > 3.5 por 7 dias |

### Advantage+ e Campaign Budget Optimization (CBO)

- **Advantage+ Shopping:** automatiza targeting e criativos. Indicado para e-commerce com catálogo e histórico de conversões.
- **CBO:** distribui budget entre ad sets automaticamente. Usar quando há 3+ ad sets competindo por mesmo objetivo.
- **Período de aprendizado:** ~50 eventos de otimização por ad set. Não alterar estrutura durante aprendizado.

---

## 3. TikTok Ads

### In-Feed Ads — Vídeo

| Especificação | Valor |
|---|---|
| Proporção | 9:16 (vertical, obrigatório para feed) |
| Resolução mínima | 720 × 1280 px |
| Resolução recomendada | 1080 × 1920 px |
| Duração | 5–60 segundos |
| Duração recomendada | 15–30 segundos |
| Formatos | MP4, MOV, AVI |
| Tamanho máximo | 500 MB |
| Frame rate | ≥ 24 fps |

### Cópia e Elementos Visuais

| Campo | Limite |
|---|---|
| Display name | máx 20 chars |
| Ad text (caption) | máx 100 chars |
| CTA | botão selecionável |
| Zona segura | Evitar texto nos 15% inferior (onde fica o CTA e handle) e 10% superior |

### Boas Práticas TikTok

- **Conteúdo nativo:** anúncios que parecem TikTok orgânico têm CTR 2–3× maior
- **Som:** TikTok é plataforma com som. Música/narração são essenciais — não o contrário do Meta
- **Hook nos primeiros 3 segundos:** usuário rola o feed mais rápido que no Instagram
- **Texto na tela:** use legendas on-screen — melhora retenção mesmo com som ativo

---

## 4. LinkedIn Ads

### Single Image Ads

| Especificação | Valor |
|---|---|
| Proporção recomendada | 1.91:1 (paisagem) ou 1:1 (quadrado) |
| Resolução mínima (paisagem) | 1200 × 628 px |
| Resolução mínima (quadrado) | 1200 × 1200 px |
| Formatos | JPG, PNG |
| Tamanho máximo | 5 MB |

### Cópia de Anúncio

| Campo | Limite |
|---|---|
| Introductory text | 150 chars (antes do "ver mais"); máx 600 chars |
| Headline | máx 70 chars |
| Description | máx 70 chars |
| CTA | botão selecionável |

### Video Ads

| Especificação | Valor |
|---|---|
| Proporção | 16:9 (paisagem), 1:1 (quadrado), 4:5 (portrait) |
| Duração | 3 segundos – 30 minutos |
| Duração recomendada | 15–30 segundos |
| Tamanho máximo | 200 MB |
| Formatos | MP4 |

### Lead Gen Forms (LGF)

| Campo | Limite |
|---|---|
| Headline | máx 60 chars |
| Details | máx 70 chars |
| CTA button | máx 20 chars |
| Campos de dados | máx 12 por formulário |
| Privacy policy URL | obrigatório |

### Segmentação LinkedIn — Contexto

| Parâmetro | Referência |
|---|---|
| Audiência mínima | 300 pessoas |
| Audiência mínima recomendada | 50.000 (Sponsored Content) |
| CPM médio | R$ 90–180 (Sponsored Content Brasil) |
| Frequência de fadiga | > 4 impressões por membro por semana |
| Matched Audiences mínimo | 300 matches (para aplicar Matched Audience) |

---

## 5. Benchmarks de Performance — Visão Geral

> **Fonte:** Dados agregados de mercado BR/LATAM 2025–2026. Use como referência para análise comparativa — a performance real varia por setor, qualidade criativa e maturidade da conta. Consulte `industry-profiles.md` para benchmarks específicos por setor.

### Google Ads — Search

| Métrica | Baixo | Médio | Alto |
|---|---|---|---|
| CTR | < 2% | 2–5% | > 5% |
| CPC médio (BR) | < R$ 1 | R$ 1–5 | > R$ 5 |
| Taxa de conversão | < 2% | 2–5% | > 5% |
| Quality Score | 1–4 | 5–7 | 8–10 |
| Impression Share | < 30% | 30–60% | > 60% |

### Google Ads — Display / Performance Max

| Métrica | Baixo | Médio | Alto |
|---|---|---|---|
| CTR (Display) | < 0.1% | 0.1–0.3% | > 0.3% |
| CPM (BR) | < R$ 5 | R$ 5–20 | > R$ 20 |
| View-through rate | < 10% | 10–25% | > 25% |

### Meta Ads (Feed)

| Métrica | Baixo | Médio | Alto |
|---|---|---|---|
| CTR (link) | < 0.8% | 0.8–2% | > 2% |
| CPM (BR) | < R$ 15 | R$ 15–40 | > R$ 40 |
| CPC (link) | < R$ 1 | R$ 1–5 | > R$ 5 |
| Frequência (7D) | — | 2–3.5 | > 3.5 = risco fadiga |
| Taxa de conversão | < 1% | 1–3% | > 3% |

### TikTok Ads

| Métrica | Baixo | Médio | Alto |
|---|---|---|---|
| CTR | < 0.5% | 0.5–1.5% | > 1.5% |
| CPM (BR) | < R$ 10 | R$ 10–30 | > R$ 30 |
| Video completion rate | < 15% | 15–35% | > 35% |

### LinkedIn Ads

| Métrica | Baixo | Médio | Alto |
|---|---|---|---|
| CTR | < 0.3% | 0.3–0.8% | > 0.8% |
| CPM (BR) | < R$ 90 | R$ 90–180 | > R$ 180 |
| Lead form completion rate | < 5% | 5–13% | > 13% |

### Sinais de Fadiga Criativa — Thresholds

| Sinal | Threshold de Alerta | Threshold Crítico |
|---|---|---|
| Queda de CTR vs baseline (7D→3D) | > 15% de queda | > 30% de queda |
| Alta de CPM vs baseline (7D→3D) | > 10% de alta | > 25% de alta |
| Frequência Meta (7 dias) | > 3.5 | > 5.0 |
| Dias em veiculação (Meta, sem refresh) | > 21 dias | > 35 dias |
| Dias em veiculação (Google Search RSA) | > 45 dias | > 90 dias |

---

## 6. Políticas de Anúncios — Restrições Críticas

> Resumo das principais restrições por plataforma. Para setores específicos (saúde, financeiro, educação), consulte também `compliance-rules.md`.

### Google Ads

| Categoria | Restrição |
|---|---|
| Conteúdo enganoso | Proibido: promessas falsas, "garantia de resultado", antes/depois tendencioso |
| Afirmações superlativas | Evitar "o melhor", "número 1" sem comprovação verificável |
| Urgência falsa | Proibido: "Apenas hoje!" sem validade real |
| Maiúsculas | Proibido uso excessivo. Ex: "CLIQUE AQUI" → reprovado |
| Pontuação excessiva | Proibido: "!!!","???" |
| Destino | Landing page deve corresponder ao anúncio. URL final não pode redirecionar para domínio diferente |
| Saúde e medicamentos | Setor restrito — requer verificação de anunciante |
| Serviços financeiros | Requer conformidade com regulamentações locais (CVM, BCB) |
| Conteúdo adulto | Proibido em campanhas padrão |

### Meta Ads

| Categoria | Restrição |
|---|---|
| Atributos pessoais | Proibido: referenciar raça, religião, saúde, orientação sexual, status financeiro do usuário |
| Antes/depois | Proibido em saúde, beleza — percepção de resultado negativo atual |
| "Você" / segunda pessoa | Evitar frases que presumam características do usuário ("Você tem diabetes?") |
| Clickbait | Proibido: "Você não vai acreditar..." headlines de curiosidade artificialmente criada |
| Texto excessivo em imagem | Permitido tecnicamente mas degrada alcance — manter minimal |
| Conteúdo restrito | Álcool, suplementos, crédito, emprego, habitação — requerem declaração de categoria especial |
| Deep fakes / IA não declarada | Proibido: rostos gerados por IA em anúncios sem declaração |

### TikTok Ads

| Categoria | Restrição |
|---|---|
| Produtos proibidos | Tabaco, armas, criptomoedas (varia por país) |
| Conteúdo de saúde | Proibido: alegações médicas sem comprovação |
| Comparação com concorrentes | Permitida mas sem denegrir — foco em benefício próprio |
| Menores de 18 | Proibido: anúncios de álcool, crédito, apostas |
| Conteúdo enganoso | Proibido: preços falsos, promoções inexistentes |

### LinkedIn Ads

| Categoria | Restrição |
|---|---|
| Conteúdo profissional | Deve manter tom profissional — conteúdo sensacionalista é reprovado |
| Discriminação | Proibido: segmentação por características protegidas para fins discriminatórios |
| Conteúdo adulto | Estritamente proibido |
| Produtos financeiros | Requer conformidade com regulamentações locais |
| Testemunhos | Devem ser reais e verificáveis |

### Restrições Setoriais Gerais (Brasil)

| Setor | Restrição Principal |
|---|---|
| Saúde / Clínicas | ANVISA: proibido prometer cura, antes/depois, depoimentos de pacientes para alguns tratamentos |
| Educação | MEC: cuidado com afirmações sobre aprovação em concursos/vestibulares sem base estatística |
| Financeiro | BACEN/CVM: proibido prometer retorno financeiro garantido |
| Imobiliário | CRECI: cuidado com valores de valorização sem lastro |
| Apostas / Jogos | SECAP: categoria especial em todas as plataformas; verificação obrigatória |
