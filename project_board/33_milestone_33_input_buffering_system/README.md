# M33: Input Buffering System

**Status:** Planning  
**Depends:** M11-M32

## Overview

Formalize input buffering beyond jump buffer. Queue next ability action while current attack plays, using cancel windows from M30 frame timing. Enables responsive combo flow.

## Key Concepts

- **Action queue**: Store next input while current action executing
- **Priority-based**: Some actions override others (jump > attack)
- **Buffer decay**: Queued input expires if not used within timeout
- **Integration with cancel windows**: Can buffer during cancel window frames

## Tickets

- 01_ability_input_queue_system
- 02_queue_priority_and_expiry
- 03_cancel_window_queue_dispatch
- 04_verify_buffer_responsiveness
