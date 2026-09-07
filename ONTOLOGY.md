# Toybox — Palantir Ontology

`toybox` is now modeled as an ontology-first software catalog. The existing `README.md` remains the human-curated source of truth; the `ontology/` and `scripts/` directories provide the machine-readable semantic layer and ingestion/validation tooling.

Palantir Foundry models real-world domains with object types, properties, link types, action types, interfaces, shared properties, and object type groups. This repository mirrors those primitives so the catalog can be mapped into Foundry without flattening it into an unstructured list.

## Object graph

```text
Category ──contains──> Tool ──runsOn────────> Platform
                         │
                         ├──hasCapability───> Capability
                         ├──hasInterface────> Interface
                         ├──hasStamp────────> Stamp
                         ├──sourcedFrom─────> Source
                         ├──governedBy──────> Policy
                         ├──alternativeTo───> Tool
                         └──dependsOn───────> Tool
```

## Object types

| API name | Purpose | Primary key |
|---|---|---|
| `Tool` | Software, service, hardware, standard, client, wrapper, utility | `toolId` |
| `Category` | Functional catalog grouping | `categoryId` |
| `Platform` | Runtime/device availability | `platformId` |
| `Capability` | Normalized function a tool provides | `capabilityId` |
| `Interface` | CLI, GUI, API, client, frontend, wrapper, adapter | `interfaceId` |
| `Stamp` | Curatorial metadata and trust signals | `stampId` |
| `Source` | Provenance for catalog facts | `sourceId` |
| `Policy` | Governance / review constraints | `policyId` |

## Link types

- `Category -> contains -> Tool` (one-to-many)
- `Tool -> runsOn -> Platform` (many-to-many)
- `Tool -> hasCapability -> Capability` (many-to-many)
- `Tool -> hasInterface -> Interface` (one-to-many)
- `Tool -> hasStamp -> Stamp` (many-to-many)
- `Tool -> sourcedFrom -> Source` (many-to-many)
- `Tool -> governedBy -> Policy` (many-to-many)
- `Tool -> alternativeTo -> Tool` (many-to-many)
- `Tool -> dependsOn -> Tool` (many-to-many)

## Interfaces

### `CatalogEntity`
Shared shape for discoverable ontology objects:

- `id`
- `name`
- `description`
- `status`
- `sourceUrl`
- `updatedAt`

### `ExecutableTool`
Behavioral contract for software that can be invoked by an application or agent:

- declares one or more `Capability` links
- declares supported `Platform` links
- declares execution mode (`local`, `web`, `api`, `cli`, `desktop`, `mobile`, `embedded`)
- declares policy requirements before governed execution

## Governed action types

| Action | Object | Effect |
|---|---|---|
| `RegisterTool` | Tool | Create a canonical catalog entry |
| `UpdateToolMetadata` | Tool | Modify approved metadata/provenance |
| `SetToolLifecycle` | Tool | Set `experimental`, `active`, `deprecated`, or `blocked` |
| `AttachCapability` | Tool/Capability | Create capability link |
| `AttachPlatform` | Tool/Platform | Create platform link |
| `AttachPolicy` | Tool/Policy | Apply governance constraint |
| `ApproveTool` | Tool | Record review/approval state |
| `DeprecateTool` | Tool | Mark a tool deprecated without deleting history |

Destructive or security-sensitive execution is intentionally not modeled as an automatic catalog action. The ontology records capabilities and governance; execution remains subject to the consuming application's permissions and policy layer.

## Files

- `ontology/schema.json` — canonical ontology definition
- `ontology/seed.json` — reusable Platform/Stamp/Policy seed objects
- `scripts/ingest_readme.py` — extracts categories/tools from the curated README into graph-ready JSON
- `scripts/validate_ontology.py` — validates ontology structure and generated data
- `.github/workflows/ontology.yml` — CI validation

## Foundry mapping

1. Materialize generated object datasets (`tools`, `categories`, `platforms`, etc.).
2. Create Foundry Object Types with the API names in `ontology/schema.json`.
3. Map primary keys and properties to those datasets.
4. Create Link Types using foreign keys or join datasets according to declared cardinality.
5. Create Action Types matching the governed action declarations.
6. Apply Foundry roles/permissions to ontology resources and object data.
7. Expose approved objects to Workshop, Object Explorer, Functions, AIP, or Ontology SDK clients.
