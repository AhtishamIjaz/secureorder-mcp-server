---
title: SecureOrder MCP
emoji: 📦
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
---

# SecureOrder-Pro MCP Server 🚀

An industrial-grade Model Context Protocol (MCP) server for secure inventory management and order processing.

## 🧠 Key Features
* **Pydantic Validation:** Strict input schemas to prevent prompt injection and malformed data.
* **Policy Enforcement:** Hardcoded business logic (e.g., shipping-status-aware cancellations).
* **Relational Database:** SQLite-backed storage with atomic transaction support.

## 🛠️ Tools Provided
| Tool | Description | Input |
| :--- | :--- | :--- |
| `search_products` | Fuzzy search the catalog | `query` (str) |
| `place_order` | Atomic inventory deduction | `customer_id`, `product_id`, `quantity` |
| `cancel_order` | Policy-aware cancellation | `order_id`, `reason` |

## 🚀 Deployment
This project is automatically built and pushed to Docker Hub via GitHub Actions.

### Local Development
1. Install `uv`
2. Run `uv sync`
3. Start server: `uv run app.py`