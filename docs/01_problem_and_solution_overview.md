# CIRO — Crisis Intelligence & Response Orchestrator
## Problem & Solution Overview

---

## 1. The Problem

### Challenge Context (AISeekho 2026 — Challenge 3)

Metropolitans in Pakistan and globally face recurring, localized crises:
- Urban flooding (seasonal, severe in Lahore, Islamabad, Karachi)
- Heatwaves
- Road blockages and traffic accidents
- Infrastructure failures (power, bridges, drainage)

**The core failure is not the lack of information — it is fragmentation.**

Critical signals exist across social media, weather APIs, map platforms, and field reports. But no system converts these signals into coordinated, actionable decisions in real time.

Response systems today are:
- **Fragmented**: NDMA, provincial authorities, military, NGOs, and emergency services each operate in silos
- **Reactive**: action begins after the crisis is already severe, not as it develops
- **Slow to coordinate**: resource allocation happens by committee, not by data-driven gap analysis
- **Communication-blind**: an NGO arriving in a flood zone has no visibility into what is already deployed or most needed

This pattern is documented across the 2010 floods, the 2022 floods (33M affected, 1,735 killed, $30B in losses), and the 2025 OCHA Flash Updates. It is structural, not incidental.

---

## 2. What Currently Does Not Exist

There is no unified platform where:
- Live signals (social, weather, maps) are automatically ingested and classified
- A confirmed crisis automatically triggers coordinated response planning
- Emergency services, agencies, and field units share a single operational picture
- Resource gaps are identified and prioritized by data, not committee
- Actions are simulated and outcomes are visible before deployment

---

## 3. Our Solution: CIRO

**CIRO is a two-layer agentic system** where the layers feed each other.

### Layer 1 — Crisis Intelligence (Signal → Detection)
Ingests multi-source signals in real time, detects emerging crises, classifies type and severity, and escalates to the response layer with full confidence reasoning.

### Layer 2 — Response Orchestration (Detection → Coordinated Action)
Takes the confirmed crisis and coordinates the actual response: resource deployment, routing, field communications, SITREP generation, and action simulation with visible outcomes.

This architecture satisfies what the challenge explicitly asks for (Layer 1) while differentiating CIRO from every other team with the depth of Layer 2.

---

## 4. Two-Audience Design

CIRO serves two audiences simultaneously:

| Audience | Interface | What They See |
|---|---|---|
| Emergency services / command | Web dashboard | Full operational picture, agent reasoning logs, resource map, dispatch orders |
| General public | Mobile app | Crisis alerts, affected zone map, safe routes, real-time status |

Both audiences consume the same underlying agent pipeline — the data is simply presented differently.

---

## 5. Demo Scenario (Fixed for Submission)

**Scenario: Urban flooding in G-10, Islamabad**

> Social media post: *"G-10 mein pani bhar gaya hai, gaariyan phans gayi hain"*  
> Weather: Heavy rainfall alert active  
> Maps: Traffic congestion spike on Srinagar Highway  

**Expected CIRO output:**

| Stage | Output |
|---|---|
| Signal detection | 3 corroborating signals identified |
| Crisis classification | Urban flooding — G-10, Islamabad — Confidence: High |
| Severity estimate | Severity 4/5 — vehicles stranded, 2 main arteries blocked |
| Action plan | Reroute traffic via Margalla Road; dispatch rescue unit from F-8; alert residents in I-10, G-9 |
| Simulated execution | Route updated on mock map; emergency ticket #2841 created; public alert sent |
| Outcome | Congestion reduced by 60% in simulation; 3 units dispatched |

---

## 6. Why This Wins

| Criterion | Weight | CIRO's Advantage |
|---|---|---|
| Google Antigravity Integration | 25% | All 6 agents orchestrated through Antigravity Manager View |
| Agentic Reasoning & Workflow | 20% | Full observe → reason → decide → act → evaluate loop visible in traces |
| Problem Understanding & Decision Quality | 20% | Two-layer architecture goes beyond detection into actual coordinated dispatch |
| Action Simulation & Outcome | 15% | Map updates, tickets, alerts, before/after congestion visible |
| Technical Implementation | 10% | FastAPI + PostGIS + OpenRouteService + Gemini 3.1 Pro |
| Innovation & UX | 10% | Dual-audience design (command + public), realistic Pakistan scenario in Urdu/English |

---

## 7. What CIRO Is Not

- Not a simple summarizer of social media
- Not a static dashboard with hardcoded rules
- Not a citizen reporting app with a "report submitted" confirmation

CIRO reasons, decides, dispatches, simulates, and shows outcomes. Every action has visible reasoning behind it.
