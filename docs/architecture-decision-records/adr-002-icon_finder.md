# ADR-002: Unreal Engine Icon Finder Utility

## Status
Completed

## Context
Unreal Engine installations contain numerous icons spread across different locations, making it difficult for developers to locate and reuse existing icons. We need a tool to discover and preview icons across multiple Unreal Engine installations.

## Decision
We will implement a cross-platform icon finder utility using Python with PySide6 and QML, structured as follows:

```
UnrealBuildTools/
├── python/
   └── unreal_build_tools/
      └── ui/
         └── icon_finder/
            ├── models/
            │   ├── icon_model.py
            │   └── filter_model.py
            ├── qml/
            │   └── main.qml
            ├── constants.py
            └── main.py
```


### Technical Details:
1. Core Components:
   - Platform utilities for engine detection
   - Icon model for managing icon data
   - Filter model for search functionality
   - Settings service for persistent preferences

2. UI Features:
   - Material Design-based QML interface
   - Grid view with adjustable icon sizes
   - Live search filtering
   - Tooltip previews
   - Copy path on click with toast notification
   - Size persistence between sessions
   - Proper macOS bundle path handling

3. Performance Features:
   - Dynamic icon loading
   - Virtual scrolling via GridView
   - Efficient path filtering
   - Common icon detection across versions

4. Cross-Platform Support:
   - Windows/Mac/Linux path handling
   - Native look and feel via Material theme
   - Platform-specific file:// URL generation

## Consequences
### Positive
- Clean separation of models and UI
- Efficient icon browsing across versions
- Platform-independent implementation
- Modern Material Design interface
- Persistent user preferences

### Negative
- Qt/QML dependency required
- More complex than a basic file browser
- Initial icon scanning delay

## Implementation Notes
- Uses PySide6 for native performance
- QML Material styling for consistency
- Model/View pattern for scalability
