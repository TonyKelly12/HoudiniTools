# Material Browser - Quick Start Guide

## Simple Installation

1. **Copy the Scripts**
   - Copy `material_browser.py` and `redshift_material_tool_v2.py` to:
   - **Windows**: `C:/Users/[your-username]/Documents/houdini[version]/scripts/python/`
   - Example: `C:/Users/John/Documents/houdini20.5/scripts/python/`

2. **Add to Houdini**
   - Open Houdini
   - Right-click on any shelf
   - Choose "New Tool..."
   - Name it: "Material Browser"
   - In the script tab, paste:
   ```python
   import material_browser
   material_browser.show_material_browser()
   ```
   - Click Accept

3. **Use the Tool**
   - Click the new "Material Browser" button on your shelf
   - Browse tab: View existing materials
   - Import tab: Add new materials

## Quick Tips

- **To Import Materials**: Use the Import tab, browse to your texture folder, click on what you want
- **To View Materials**: Use the Browse tab to see what's already in your project
- **Icons**: Put an `icon.jpg` file in your texture folders for previews

That's it! You're ready to use the Material Browser.