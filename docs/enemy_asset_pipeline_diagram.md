# Enemy Asset Pipeline Diagram

## Simple Pipeline

``` mermaid
flowchart TD
    A[Design enemy families and mutation drops] --> B[Write Blender enemy generator recipes]
    B --> C[Generate low-poly enemy variants in Blender]
    C --> D[Export each enemy as .glb]
    D --> E[Place exports in Godot project folder]
    E --> F[Run Godot enemy scene generator tool]
    F --> G[Auto-create wrapper .tscn scenes]
    G --> H[Attach shared enemy base script]
    H --> I[Assign metadata from filename]
    I --> J[Add collision, hurtbox, and markers]
    J --> K[Open key enemies for manual tweaks]
    K --> L[Hook up family-specific AI and tuning]
    L --> M[Place enemies into prototype levels]
    M --> N[Playtest mutation drops and encounter design]
    N --> O{Needs changes?}
    O -->|Art changes| B
    O -->|Behavior changes| L
    O -->|Level changes| M
    O -->|Feels good| P[Lock content and expand roster]
```

## Detailed Pipeline

``` mermaid
flowchart LR
    subgraph Blender
        A1[Enemy recipe function]
        A2[Primitive parts library]
        A3[Randomized variant generation]
        A4[Export .glb files]
        A1 --> A3
        A2 --> A3
        A3 --> A4
    end

    subgraph Godot Import
        B1[generated_glb folder]
        B2[Import .glb assets]
        B3[Run scene generator script]
        B4[Create .tscn wrapper scenes]
        B5[Add collision and hurtbox]
        B6[Add markers and metadata]
        B1 --> B2 --> B3 --> B4 --> B5 --> B6
    end

    subgraph Gameplay
        C1[Attach enemy base script]
        C2[Assign mutation drop]
        C3[Add family-specific behavior]
        C4[Place in levels]
        C5[Playtest]
        C6[Iterate]
        C1 --> C2 --> C3 --> C4 --> C5 --> C6
    end

    A4 --> B1
    B6 --> C1
    C6 --> A1
```
