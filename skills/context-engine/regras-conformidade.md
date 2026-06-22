# Referência de Regras de Conformidade (Compliance)

Este arquivo é o conjunto de regras de conformidade canônico para o mktOS. Todos os módulos de marketing DEVEM verificar as saídas contra estas regras antes da entrega. As regras são estruturadas para consumo programático pelo motor de contexto.

---

## Seção 1: Leis de Privacidade Geográfica

### 1.1 Brasil — Lei Geral de Proteção de Dados (LGPD)

| Campo | Detalhe |
|---|---|
| **Região** | Brasil |
| **Lei** | Lei Geral de Proteção de Dados Pessoais (Lei nº 13.709/2018) |
| **Vigência** | Promulgada em 2018; em vigor desde setembro de 2020; sanções desde agosto de 2021. |
| **Modelo de Consentimento** | Opt-in. O consentimento deve ser livre, informado e inequívoco para uma finalidade específica. O interesse legítimo é uma base alternativa, mas exige um Teste de Ponderação (LIA) documentado. |
| **Regras de E-mail** | Base legal (consentimento ou legítimo interesse) obrigatória. O descadastro (unsubscribe) deve ser fácil e imediato. Titulares têm direitos de acesso, correção e exclusão. |
| **Cookies/Rastreamento** | Orientações da ANPD exigem consentimento para cookies não essenciais. Banners de cookies com opções de aceitar/rejeitar são o padrão de mercado. |
| **Penalidades** | Até 2% do faturamento no Brasil, limitada a R$ 50 milhões por infração. A ANPD pode aplicar advertências e bloqueio de dados. |
| **Impacto no Marketing** | Nomeação de DPO (Encarregado de Dados) é obrigatória. Avisos de privacidade em português. Transferências internacionais exigem salvaguardas contratuais. |

### 1.2 União Europeia — GDPR

| Campo | Detalhe |
|---|---|
| **Lei** | General Data Protection Regulation (GDPR) |
| **Modelo de Consentimento** | Opt-in explícito e granular. O padrão mais rigoroso do mundo. |
| **Impacto no Marketing** | Double opt-in é o padrão da indústria. Formulários de lead precisam de caixas de seleção desmarcadas por padrão. |

### 1.3 Estados Unidos (Federal) — CAN-SPAM Act

| Campo | Detalhe |
|---|---|
| **Lei** | CAN-SPAM Act (2003) |
| **Modelo de Consentimento** | Opt-out. Não exige consentimento prévio para envio, mas o descadastro deve ser honrado em 10 dias úteis. Proibido assuntos enganosos. |

---

## Seção 2: Regulamentações por Setor (Brasil)

### 2.1 Saúde — CFM / ANVISA

| Setor | Saúde, Clínicas, Médicos, Indústria Farmacêutica |
|---|---|
| **Regulador** | Conselho Federal de Medicina (CFM) e ANVISA |
| **Proibições** | Proibido fotos de "antes e depois", mesmo com autorização. Proibido garantir cura ou resultados. Proibido anunciar equipamentos como diferencial de superioridade. |
| **Exigências** | Nome do médico e CRM devem estar visíveis em todas as peças. Divulgação de especialidade apenas se registrada (RQE). |

### 2.2 Jurídico — OAB (Código de Ética)

| Setor | Advogados e Sociedades de Advogados |
|---|---|
| **Regulador** | Ordem dos Advogados do Brasil (OAB) - Provimento 205/2021 |
| **Proibições** | Proibida a mercantilização (ex: "contrate agora", "promoção"). Proibido anunciar preços ou formas de pagamento. Proibida a captação indevida de clientela. |
| **Permitido** | Marketing de conteúdo jurídico informativo e educativo. Patrocínio de posts (tráfego pago) é permitido desde que informativo. |

### 2.3 Publicidade Geral — CONAR

| Setor | Todos os setores |
|---|---|
| **Regulador** | Conselho Nacional de Autorregulamentação Publicitária (CONAR) |
| **Regras** | A publicidade deve ser honesta e verdadeira. Publicidade comparativa é permitida apenas com critérios objetivos. Identificação publicitária deve ser clara (ex: #publi, #propaganda). |

---

## Seção 3: Regras de Acessibilidade (WCAG 2.1)

Todas as entregas do mktOS devem buscar conformidade com o nível AA da WCAG 2.1:
- **Contraste**: Mínimo de 4.5:1 para texto normal.
- **Alt Text**: Todas as imagens devem ter texto alternativo descritivo.
- **Hierarquia**: Uso correto de H1, H2, H3 para leitores de tela.
- **Legendas**: Obrigatórias para todos os conteúdos em vídeo.

---

## Aplicação das Regras

O motor de contexto aplica as regras nesta ordem de prioridade:
1. **Lei Geográfica** (ex: LGPD se o mercado for Brasil).
2. **Regulamentação do Setor** (ex: CFM se for médico).
3. **Regras da Plataforma** (ex: Políticas do Google Ads).
4. **Acessibilidade**.

### Níveis de Severidade

| Nível | Ação |
|---|---|
| **BLOCK (BLOQUEIO)** | A violação é ilegal ou causaria banimento. O plugin não gerará a saída e avisará o usuário. |
| **WARN (AVISO)** | Possível violação. O plugin gera a saída com um aviso destacado para revisão humana. |
| **SUGGEST (SUGESTÃO)** | Melhor prática que reduz riscos, mas não é obrigatória por lei. |

---
*Este documento foi adaptado por Rafael Dantas para o contexto brasileiro no mktOS v0.1.0.*
