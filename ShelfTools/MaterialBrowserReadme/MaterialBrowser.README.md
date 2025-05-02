# Material Browser & Importer for Houdini

A comprehensive material browser and importer tool for Houdini that supports hierarchical folder structures, with integrated Redshift material creation capabilities.

![Material Browser](icon.png)

## Features

### 🔍 Browse Tab
- Visual material browser with icon previews
- Supports nested folder structures within /mat context
- Automatic icon detection from texture folders
- Filter materials by name
- Double-click to open in network editor
- Right-click context menu for quick actions
- Automatic material assignment to selected objects

### 📥 Import Tab
- Smart texture folder scanner with hierarchical organization
- Support for complex nested structures (collections, variants, meshes)
- Visual differentiation of folder types with color coding
- Icon inheritance from parent folders
- Preview before import with detailed information
- Automatic Redshift material creation
- Maintains source folder hierarchy in project

### 🎨 Folder Hierarchy Support
- **Collections**: Top-level folders (gold color)
- **Variants**: Second-level folders (light blue)
- **Meshes**: Individual material folders (white)
- **Icon Inheritance**: Subfolders inherit icons from parents if not present

## Installation

1. **Copy the Python script**:
   - Save `material_browser.py` to your Houdini scripts folder:
     - Windows: `C:/Users/[username]/Documents/houdini[version]/scripts/python/`
     - Mac: `~/Library/Preferences/houdini/[version]/scripts/python/`
     - Linux: `~/houdini[version]/scripts/python/`

2. **Dependencies**:
   - Ensure `redshift_material_tool_v2.py` is in the same folder
   - Requires PySide2 (included with Houdini)
   - Requires Redshift for material creation

3. **Add to Shelf**:
   - Right-click on any shelf
   - Select "New Tool..."
   - Name: "Material Browser"
   - Script tab:
   ```python
   import material_browser
   material_browser.show_material_browser()
   ```

## Usage

### Browse Existing Materials
1. Launch the Material Browser from your shelf
2. Navigate through your existing materials in the /mat context
3. Double-click to open materials in the network editor
4. Right-click for additional options

### Import New Materials
1. Switch to the Import tab
2. Browse to your source texture folder
3. View hierarchical organization of texture sets
4. Click on items to import:
   - **Collections**: Import entire hierarchy
   - **Variants**: Import specific variant and its meshes
   - **Individual Meshes**: Import single material

### Texture Folder Structure
The tool recognizes and preserves complex folder structures:

```
SourceTextures/
├── DrumSet/                    # Collection (gold)
│   ├── 2DrumSet/              # Variant (light blue)
│   │   ├── icon.jpg           
│   │   ├── Drum1/             # Mesh (white)
│   │   │   ├── basecolor.exr
│   │   │   ├── normal.exr
│   │   │   └── roughness.exr
│   │   └── Drum2/
│   │       └── textures...
│   └── 3DrumSet/              # Another variant
│       └── meshes...
└── CharacterSet/              # Another collection
    └── variants...
```

### Icon Support
- Place `icon.jpg`, `icon.jpeg`, or `icon.png` in folders
- Subfolders automatically inherit parent icons
- Icons are displayed in 200x200 pixel previews

### Search & Filter
- Use the filter field to search materials
- Filter maintains hierarchy visibility
- Search works across all nested levels

## Material Creation

The tool automatically creates Redshift materials with proper connections for:
- Base Color
- Roughness
- Metallic
- Normal Maps
- Bump Maps
- Displacement
- Emission
- Ambient Occlusion
- Translucency
- Alpha/Opacity

## Tips & Best Practices

1. **Organize Source Files**: Structure your texture folders hierarchically for best results
2. **Use Icons**: Place icon files in collection/variant folders for visual identification
3. **Naming Conventions**: Use clear, descriptive names for folders
4. **Batch Import**: Import entire collections to maintain organization
5. **Use Filters**: Quickly find materials with the search functionality

## Troubleshooting

### Common Issues

1. **Materials not showing up**: 
   - Check your /mat context path
   - Ensure Redshift nodes are available
   - Verify texture folder paths

2. **Icons not displaying**:
   - Check file formats (jpg, jpeg, png)
   - Ensure proper file naming (icon.jpg)
   - Verify file permissions

3. **Import errors**:
   - Check write permissions in project folder
   - Ensure source textures are accessible
   - Verify Redshift is properly installed

## Version History

- **v2.0**: Added hierarchical folder support, improved UI
- **v1.0**: Initial release with basic browsing and import

## Credits

Developed for Houdini artists who work with complex material libraries and Redshift rendering.

## License

This tool is provided as-is for use within Houdini. Feel free to modify and adapt it to your needs.