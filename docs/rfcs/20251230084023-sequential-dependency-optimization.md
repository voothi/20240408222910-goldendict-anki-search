# 20251230084023 - Sequential Dependency Optimization

## Status
Staging: Approved
ZID: 20251230084023

## Description
Improving search performance by optimizing the sequential dependency between finding card IDs and retrieving card information. This RFC introduces modes to skip the second request or combine both into one, depending on the environment and requirements.

## Implementation Details

### Analytics
The standard AnkiConnect workflow for retrieving full card data requires two sequential HTTP requests:
1. `findCards`: Search query -> Card IDs.
2. `cardsInfo`: Card IDs -> Field data.

This "Sequential Dependency Problem" adds round-trip time (RTT) overhead. In environments with high latency or under frequent script execution, this overhead becomes significant.

### Decisions
1. **Compatibility First**: The default behavior remains unchanged. It executes two requests to ensure compatibility with standard AnkiConnect installations.
2. **`--only-ids` Flag**: Renamed from an initial `--fast` proposal for better semantic clarity. It terminates the workflow after the first request, returning only the card IDs. This is optimal for existence checks or when full details are not needed.
3. **`--optimized` Flag**: Leverages the custom `findCardsInfo` endpoint available in the `kardenwort-ankiconnect` fork. This combines the search and data retrieval into a single server-side operation, reducing the network overhead to a single request.

### Performance Impact
- **Default**: 2 Requests (High overhead).
- **`--only-ids`**: 1 Request (Minimal data).
- **`--optimized`**: 1 Request (Full data, requires custom add-on).

## User Review Required
> [!NOTE]
> The `--optimized` mode requires the `kardenwort-ankiconnect` fork of the AnkiConnect add-on to be installed in Anki. Standard versions will return an "unsupported action" error.
