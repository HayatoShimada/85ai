# WebSocket & State Synchronization

## State Machine

All devices (iPad, Projector) are synchronized via WebSocket:

```
IDLE → PREFERENCE → CAMERA_ACTIVE → ANALYZING → RESULT → IDLE
```

State transitions are triggered by the iPad operator UI and relayed to the projector display.

## Key Files

### `backend/services/projection_manager.py`
- `ProjectionManager` singleton — State sync + mirror frame broadcaster
- Single display WebSocket endpoint: `/ws/projection/display`
- Carries **both** JSON control messages and base64 mirror frames on the same connection
- JSON messages: state updates, recommendation data, selected tags
- Base64 frames: mirror camera output for real-time display

### `backend/routers/projection.py`
- WebSocket endpoints for projection control
- `/ws/projection/display` — Main projection display connection
- Handles connection lifecycle, message routing

### Frontend WebSocket Hooks
- **`hooks/useProjectionSync.ts`** — iPad → Backend state sync (pending message queue pattern)
- **`app/projection/page.tsx`** — Projector display WebSocket consumer

## Single WebSocket Pattern

The projector display uses a single WebSocket that multiplexes two data types:

```
Frontend distinguishes message type by checking:
- Starts with `{` → JSON control message (parse as JSON)
- Otherwise → base64 mirror frame (display as image)
```

This avoids managing two separate WebSocket connections and simplifies reconnection logic.

## Projection Payload Structure

```typescript
interface ProjectionPayload {
  appState: AppState;
  selectedTags: string[];
  userName?: string;
  capturedImage?: string;        // base64 JPEG
  recommendation?: ClothingAnalysis;
  analyzeTimedOut?: boolean;
}
```

## Reconnection

Both iPad and projector WebSocket connections auto-reconnect with a 3-second delay on disconnect.
