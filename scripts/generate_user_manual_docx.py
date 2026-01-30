"""
Generate MARS User Manual as a Word document with placeholder images.
Run this script to create MARS_USER_MANUAL.docx in the project root.
"""

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

# Output path
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'MARS_USER_MANUAL.docx')


def set_cell_shading(cell, color):
    """Set cell background color."""
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color)
    cell._tc.get_or_add_tcPr().append(shading)


def add_placeholder_image(doc, caption, width_inches=5.5, height_inches=2.5):
    """Add a placeholder box with caption text."""
    # Create a table to simulate a placeholder box
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    
    # Set cell dimensions and styling
    set_cell_shading(cell, 'E8E8E8')  # Light gray background
    
    # Add placeholder text
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"\n\n[IMAGE PLACEHOLDER]\n\n{caption}\n\n")
    run.font.size = Pt(10)
    run.font.italic = True
    run.font.color.rgb = RGBColor(100, 100, 100)
    
    # Set cell width
    cell.width = Inches(width_inches)
    
    doc.add_paragraph()  # Add spacing after


def add_heading(doc, text, level):
    """Add a heading with proper formatting."""
    heading = doc.add_heading(text, level=level)
    if level == 0:
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return heading


def add_table(doc, headers, rows):
    """Add a formatted table."""
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    
    # Add header row
    header_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        header_cells[i].text = header
        set_cell_shading(header_cells[i], '5B9BD5')  # Blue header
        for paragraph in header_cells[i].paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(10)
    
    # Add data rows
    for row_data in rows:
        row = table.add_row()
        for i, cell_text in enumerate(row_data):
            row.cells[i].text = str(cell_text)
            for paragraph in row.cells[i].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(10)
    
    doc.add_paragraph()  # Spacing after table


def create_manual():
    """Create the complete user manual document."""
    doc = Document()
    
    # Set default font
    style = doc.styles['Normal']
    style.font.name = 'Arial'
    style.font.size = Pt(10)
    
    # ==================== TITLE PAGE ====================
    doc.add_paragraph()
    doc.add_paragraph()
    title = doc.add_heading('MARS: Modal Analysis Response Solver', 0)
    subtitle = doc.add_paragraph('Complete User Manual')
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in subtitle.runs:
        run.font.size = Pt(16)
        run.font.italic = True
    
    doc.add_paragraph()
    doc.add_paragraph()
    
    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info.add_run('Audience: ').bold = True
    info.add_run('Mechanical and structural engineers using MARS via the desktop GUI\n\n')
    info.add_run('Format: ').bold = True
    info.add_run('Designed for print with mockup images for each section')
    
    doc.add_page_break()
    
    # ==================== TABLE OF CONTENTS ====================
    add_heading(doc, 'Table of Contents', 1)
    
    toc_items = [
        ('PART I: INTRODUCTION AND GETTING STARTED', [
            'Chapter 1 – Welcome to MARS',
            'Chapter 2 – System Requirements and Installation',
            'Chapter 3 – Interface Overview',
        ]),
        ('PART II: MAIN WINDOW TAB – INPUT AND SOLVER CONFIGURATION', [
            'Chapter 4 – Setting Up Your Project Directory',
            'Chapter 5 – Loading Modal Coordinate Files (.mcf)',
            'Chapter 6 – Loading Modal Stress Files (.csv)',
            'Chapter 7 – Optional: Including Steady-State Stress',
            'Chapter 8 – Optional: Including Deformations',
            'Chapter 9 – Selecting Analysis Outputs',
            'Chapter 10 – Skip First n Modes',
            'Chapter 11 – Time History Mode (Single Node Analysis)',
            'Chapter 12 – Plasticity Correction (Advanced Feature)',
            'Chapter 13 – Running the Solver',
            'Chapter 14 – Advanced Settings (Performance Tuning)',
        ]),
        ('PART III: DISPLAY TAB – 3D VISUALIZATION AND ANALYSIS', [
            'Chapter 15 – Display Tab Overview',
            'Chapter 16 – Visualization Controls (Detailed)',
            'Chapter 17 – Time Point Controls (Detailed)',
            'Chapter 18 – Animation Controls (Detailed)',
            'Chapter 19 – PyVista 3D Viewer Interaction',
            'Chapter 20 – Right-Click Context Menu (Complete Reference)',
            'Chapter 21 – Hotspot Analysis Workflow',
            'Chapter 22 – Animation Workflow',
        ]),
        ('PART IV: EXPORT AND DATA MANAGEMENT', [
            'Chapter 23 – Exporting Results to CSV',
            'Chapter 24 – APDL Initial Condition Export',
        ]),
        ('PART V: TROUBLESHOOTING AND REFERENCE', [
            'Chapter 25 – Troubleshooting Guide',
            'Chapter 26 – File Format Reference',
            'Chapter 27 – Keyboard and Mouse Reference',
            'Chapter 28 – FAQs',
            'Chapter 29 – Getting Help',
        ]),
    ]
    
    for part_name, chapters in toc_items:
        p = doc.add_paragraph()
        run = p.add_run(part_name)
        run.bold = True
        run.font.size = Pt(10)
        
        for chapter in chapters:
            p = doc.add_paragraph(chapter, style='List Bullet')
            for run in p.runs:
                run.font.size = Pt(10)
    
    doc.add_page_break()
    
    # ==================== PART I ====================
    add_heading(doc, 'PART I: INTRODUCTION AND GETTING STARTED', 1)
    doc.add_paragraph()
    
    # Chapter 1
    add_heading(doc, 'Chapter 1 – Welcome to MARS', 2)
    
    doc.add_paragraph(
        'MARS (Modal Analysis Response Solver) is a desktop application designed for post-processing '
        'modal analysis results from finite element simulations. The software transforms modal coordinates '
        'and modal stress data into comprehensive engineering outputs including stress field reconstruction, '
        'time history analysis, animations, and data exports.'
    )
    
    doc.add_paragraph()
    add_heading(doc, 'What MARS Can Do For You', 3)
    
    add_table(doc, ['Capability', 'Description'], [
        ['Stress Reconstruction', 'Combine modal coordinates with modal stress to reconstruct full stress tensor fields'],
        ['Principal Stress Analysis', 'Calculate maximum and minimum principal stresses (σ₁ and σ₃)'],
        ['Von Mises Stress', 'Compute equivalent von Mises stress for ductile material failure analysis'],
        ['Kinematic Analysis', 'Extract deformation, velocity, and acceleration from modal displacement data'],
        ['Time History Plots', 'Generate time series plots for any selected node'],
        ['3D Visualization', 'Interactive PyVista-based 3D viewing with scalar field color mapping'],
        ['Animations', 'Create animated visualizations showing stress or deformation evolution'],
        ['Hotspot Detection', 'Automatically identify nodes with critical stress values'],
        ['Data Export', 'Save results to CSV and export velocity initial conditions in APDL format'],
        ['Plasticity Correction', 'Apply Neuber or Glinka correction for localized yielding'],
    ])
    
    add_placeholder_image(doc, 'MARS main window screenshot showing the complete interface with tabs, navigator, and console')
    
    doc.add_page_break()
    
    # Chapter 2
    add_heading(doc, 'Chapter 2 – System Requirements and Installation', 2)
    
    add_heading(doc, 'Prerequisites', 3)
    p = doc.add_paragraph()
    p.add_run('• Python: ').bold = True
    p.add_run('Version 3.10 or higher\n')
    p.add_run('• Operating System: ').bold = True
    p.add_run('Windows 10/11 (primary), Linux/macOS (compatible)\n')
    p.add_run('• RAM: ').bold = True
    p.add_run('Minimum 8 GB; 16+ GB recommended for large models\n')
    
    add_heading(doc, 'Installation Steps', 3)
    doc.add_paragraph('1. Create a virtual environment: python -m venv .venv')
    doc.add_paragraph('2. Activate the virtual environment')
    doc.add_paragraph('3. Install dependencies: pip install -r requirements.txt')
    doc.add_paragraph('4. Launch MARS: python -m src.main')
    
    add_placeholder_image(doc, 'Terminal showing successful launch of MARS application')
    
    doc.add_page_break()
    
    # Chapter 3
    add_heading(doc, 'Chapter 3 – Interface Overview', 2)
    
    doc.add_paragraph(
        'The MARS interface consists of several key components that work together to provide a seamless analysis workflow.'
    )
    
    add_heading(doc, 'Main Window Components', 3)
    add_table(doc, ['Component', 'Location', 'Purpose'], [
        ['Menu Bar', 'Top', 'Access File, View, and Settings menus'],
        ['Navigator Panel', 'Left side', 'Browse and select project files'],
        ['Main Window Tab', 'Center (Tab 1)', 'Load files, configure analysis, run solver'],
        ['Display Tab', 'Center (Tab 2)', '3D visualization, animation, exports'],
        ['Console', 'Bottom of Main Window', 'View status messages and processing logs'],
    ])
    
    add_placeholder_image(doc, 
        'Annotated interface image with numbered callouts:\n'
        '1. Menu Bar  2. Navigator Panel  3. Tab Buttons\n'
        '4. File Input Section  5. Output Options Section\n'
        '6. Console/Plot Tabs  7. Progress Bar  8. SOLVE Button'
    )
    
    doc.add_page_break()
    
    # ==================== PART II ====================
    add_heading(doc, 'PART II: MAIN WINDOW TAB – INPUT AND SOLVER CONFIGURATION', 1)
    doc.add_paragraph()
    
    # Chapter 4
    add_heading(doc, 'Chapter 4 – Setting Up Your Project Directory', 2)
    
    doc.add_paragraph(
        'The Navigator panel provides quick access to your project files. '
        'MARS automatically filters the view to show only relevant file types.'
    )
    
    add_heading(doc, 'Selecting a Project Directory', 3)
    doc.add_paragraph('1. Click File → Select Project Directory from the menu bar')
    doc.add_paragraph('2. Navigate to the folder containing your analysis files')
    doc.add_paragraph('3. Click Select Folder to confirm')
    
    add_heading(doc, 'Supported File Types', 3)
    add_table(doc, ['Extension', 'Description'], [
        ['.mcf', 'Modal Coordinate Files'],
        ['.csv', 'Modal Stress Files, Deformation Files'],
        ['.txt', 'Steady-State Stress Files'],
    ])
    
    add_placeholder_image(doc, 'Navigator panel showing example project files with .mcf, .csv, and .txt files listed')
    
    doc.add_page_break()
    
    # Chapter 5
    add_heading(doc, 'Chapter 5 – Loading Modal Coordinate Files (.mcf)', 2)
    
    doc.add_paragraph(
        'The modal coordinate file contains the time-varying amplitudes of each mode shape from your transient analysis.'
    )
    
    add_heading(doc, 'Loading Procedure', 3)
    doc.add_paragraph('1. In the File Inputs section, click Read Modal Coordinate File (.mcf)')
    doc.add_paragraph('2. Select your .mcf file from the file dialog')
    doc.add_paragraph('3. The file path appears in the text field next to the button')
    doc.add_paragraph('4. Check the Console for validation messages')
    
    add_heading(doc, 'File Format Requirements', 3)
    doc.add_paragraph('• Must contain a "Time" column (in seconds)')
    doc.add_paragraph('• Additional columns represent modal coordinates (one per mode)')
    doc.add_paragraph('• First row contains headers')
    
    add_placeholder_image(doc, 'File Input section with modal coordinate file loaded, showing the file path and success message in console')
    
    doc.add_page_break()
    
    # Chapter 6
    add_heading(doc, 'Chapter 6 – Loading Modal Stress Files (.csv)', 2)
    
    doc.add_paragraph(
        'The modal stress file contains stress tensors for each mode at every node in your model.'
    )
    
    add_heading(doc, 'Required Columns', 3)
    add_table(doc, ['Column Pattern', 'Description'], [
        ['NodeID', 'Unique node identifier'],
        ['sx_1, sx_2, ...', 'Normal stress X per mode'],
        ['sy_1, sy_2, ...', 'Normal stress Y per mode'],
        ['sz_1, sz_2, ...', 'Normal stress Z per mode'],
        ['sxy_1, sxy_2, ...', 'Shear stress XY per mode'],
        ['syz_1, syz_2, ...', 'Shear stress YZ per mode'],
        ['sxz_1, sxz_2, ...', 'Shear stress XZ per mode'],
    ])
    
    add_heading(doc, 'Optional Columns', 3)
    doc.add_paragraph('• X, Y, Z – Node coordinates for 3D visualization')
    
    add_placeholder_image(doc, 'Example stress CSV structure showing NodeID, coordinates, and stress component columns')
    
    doc.add_page_break()
    
    # Chapter 7
    add_heading(doc, 'Chapter 7 – Optional: Including Steady-State Stress', 2)
    
    doc.add_paragraph(
        'If your structure has a static pre-stress condition (thermal stress, bolt preload, etc.), '
        'you can include it in the analysis.'
    )
    
    add_heading(doc, 'Enabling Steady-State Stress', 3)
    doc.add_paragraph('1. Check the box Include Steady-State Stress Field (Optional)')
    doc.add_paragraph('2. The steady-state file input section appears')
    doc.add_paragraph('3. Click Read Full Stress Tensor File (.txt)')
    doc.add_paragraph('4. Select your steady-state stress file')
    
    add_heading(doc, 'Effect on Results', 3)
    doc.add_paragraph('• Steady-state stress is added to the reconstructed transient stress at each time step')
    doc.add_paragraph('• Affects all stress-based outputs (Von Mises, Principal Stresses)')
    doc.add_paragraph('• Important for accurate fatigue analysis with mean stress effects')
    
    add_placeholder_image(doc, 'Steady-state stress toggle checked, with file input field showing loaded file path')
    
    doc.add_page_break()
    
    # Chapter 8
    add_heading(doc, 'Chapter 8 – Optional: Including Deformations', 2)
    
    doc.add_paragraph(
        'Loading modal deformations unlocks kinematic analysis capabilities including '
        'deformation magnitude, velocity, and acceleration.'
    )
    
    add_heading(doc, 'Enabling Deformations', 3)
    doc.add_paragraph('1. Check the box Include Deformations (Optional)')
    doc.add_paragraph('2. The deformation file input section appears')
    doc.add_paragraph('3. Click Read Modal Deformations File (.csv)')
    doc.add_paragraph('4. Select your deformation CSV file')
    
    add_heading(doc, 'Unlocked Outputs', 3)
    doc.add_paragraph('After loading deformations, these outputs become available:')
    doc.add_paragraph('• Deformation – Displacement magnitude over time')
    doc.add_paragraph('• Velocity – Time derivative of displacement')
    doc.add_paragraph('• Acceleration – Time derivative of velocity')
    doc.add_paragraph('• Animated deformed shape – Visual mesh deformation in Display tab')
    
    add_placeholder_image(doc, 'Deformation toggle checked, showing the deformation file input section')
    
    doc.add_page_break()
    
    # Chapter 9
    add_heading(doc, 'Chapter 9 – Selecting Analysis Outputs', 2)
    
    doc.add_paragraph(
        'The Output Options section allows you to specify which results to compute. '
        'Multiple outputs can be selected simultaneously.'
    )
    
    add_heading(doc, 'Available Outputs', 3)
    add_table(doc, ['Output', 'Description', 'Requirements'], [
        ['Max Principal Stress', 'Maximum principal stress (σ₁) envelope', 'Stress file'],
        ['Min Principal Stress', 'Minimum principal stress (σ₃) envelope', 'Stress file'],
        ['Von-Mises Stress', 'Equivalent stress for ductile failure', 'Stress file'],
        ['Deformation', 'Displacement magnitude', 'Deformation file'],
        ['Velocity', 'Velocity magnitude', 'Deformation file'],
        ['Acceleration', 'Acceleration magnitude', 'Deformation file'],
        ['Enable Time History Mode', 'Plot time series for a single node', 'Any output'],
        ['Enable Plasticity Correction', 'Apply notch plasticity methods', 'Von-Mises selected'],
    ])
    
    add_placeholder_image(doc, 'Output Options section with checkboxes, some checked (Von-Mises, Max Principal Stress, Deformation)')
    
    doc.add_page_break()
    
    # Chapter 10
    add_heading(doc, 'Chapter 10 – Skip First n Modes', 2)
    
    doc.add_paragraph(
        'This feature allows you to exclude the first n modes from the analysis – '
        'useful for omitting rigid-body modes or modes with erroneous data.'
    )
    
    add_heading(doc, 'When to Use This Feature', 3)
    add_table(doc, ['Scenario', 'Recommended Setting'], [
        ['Fixed boundary model (no rigid-body motion)', '0 (include all modes)'],
        ['Free-free model (6 rigid-body modes)', '6 (skip rigid-body modes)'],
        ['First mode has corrupted data', '1 or more as needed'],
    ])
    
    add_heading(doc, 'Important Notes', 3)
    doc.add_paragraph('• Skipped modes are completely excluded from stress/displacement reconstruction')
    doc.add_paragraph('• Verify with your FEA tool which modes are rigid-body modes')
    doc.add_paragraph('• Over-skipping will miss significant modal contributions')
    
    add_placeholder_image(doc, 'Skip first n modes dropdown showing options 0-6')
    
    doc.add_page_break()
    
    # Chapter 11
    add_heading(doc, 'Chapter 11 – Time History Mode (Single Node Analysis)', 2)
    
    doc.add_paragraph(
        'Time History Mode computes and plots the time series of a selected output quantity for a specific node.'
    )
    
    add_heading(doc, 'Enabling Time History Mode', 3)
    doc.add_paragraph('1. Check Enable Time History Mode (Single Node)')
    doc.add_paragraph('2. The Scoping section becomes active')
    doc.add_paragraph('3. Enter the desired Node ID in the input field')
    doc.add_paragraph('4. Select exactly one output type (Von-Mises, Max Principal, etc.)')
    
    add_heading(doc, 'Running Time History Analysis', 3)
    doc.add_paragraph('1. Click SOLVE')
    doc.add_paragraph('2. The solver computes the full time history for the specified node')
    doc.add_paragraph('3. Results appear in the Plot (Time History) tab')
    
    add_placeholder_image(doc, 'Time History plot showing Von-Mises stress over time for a selected node, with peak value labeled')
    
    doc.add_page_break()
    
    # Chapter 12
    add_heading(doc, 'Chapter 12 – Plasticity Correction (Advanced Feature)', 2)
    
    doc.add_paragraph(
        'For structures with stress concentrations where elastic stress exceeds yield, '
        'plasticity correction provides more realistic stress and strain estimates.'
    )
    
    add_heading(doc, 'Available Methods', 3)
    add_table(doc, ['Method', 'Description', 'Use Case'], [
        ['Neuber', 'Classic hyperbolic correction', 'General notches, faster computation'],
        ['Glinka', 'Energy-based ESED method', 'More conservative, thick sections'],
    ])
    
    add_heading(doc, 'Enabling Plasticity Correction', 3)
    doc.add_paragraph('1. Select Von-Mises Stress as an output (required)')
    doc.add_paragraph('2. Check Enable Plasticity Correction')
    doc.add_paragraph('3. The plasticity options section appears')
    doc.add_paragraph('4. Select a method (Neuber or Glinka)')
    doc.add_paragraph('5. Click Enter Material Profile to define stress-strain curves')
    doc.add_paragraph('6. Load a Temperature Field File (CSV with NodeID and Temperature)')
    
    add_heading(doc, 'Output Files', 3)
    doc.add_paragraph('• corrected_von_mises.csv – Corrected stress values')
    doc.add_paragraph('• plastic_strain.csv – Equivalent plastic strain at each node')
    doc.add_paragraph('• time_of_max_corrected_von_mises.csv – Time of peak corrected stress')
    
    add_placeholder_image(doc, 'Plasticity Correction panel showing method selection, material profile button, and temperature field input')
    
    doc.add_page_break()
    
    # Chapter 13
    add_heading(doc, 'Chapter 13 – Running the Solver', 2)
    
    doc.add_paragraph(
        'After configuring all inputs and options, the SOLVE button initiates the computation.'
    )
    
    add_heading(doc, 'Pre-Run Checklist', 3)
    doc.add_paragraph('☐ Modal coordinate file loaded')
    doc.add_paragraph('☐ Modal stress file loaded')
    doc.add_paragraph('☐ (Optional) Steady-state stress file loaded')
    doc.add_paragraph('☐ (Optional) Deformation file loaded')
    doc.add_paragraph('☐ At least one output selected')
    doc.add_paragraph('☐ Skip modes set appropriately')
    doc.add_paragraph('☐ (If Time History) Node ID entered')
    
    add_heading(doc, 'Running the Analysis', 3)
    doc.add_paragraph('1. Click the SOLVE button')
    doc.add_paragraph('2. Monitor the Progress Bar for completion status')
    doc.add_paragraph('3. Watch the Console for processing messages')
    doc.add_paragraph('4. Wait for the "Analysis complete" confirmation')
    
    add_placeholder_image(doc, 'SOLVE button with progress bar at 75%, console showing processing messages')
    
    doc.add_page_break()
    
    # Chapter 14
    add_heading(doc, 'Chapter 14 – Advanced Settings (Performance Tuning)', 2)
    
    doc.add_paragraph('Access advanced settings via Settings → Advanced in the menu bar.')
    
    add_heading(doc, 'RAM Allocation', 3)
    add_table(doc, ['Setting', 'Range', 'Recommendation'], [
        ['RAM Allocation (%)', '10% - 95%', 'Default: 70%'],
    ])
    doc.add_paragraph('• Increase to 90%: For very large models (>1M data points)')
    doc.add_paragraph('• Decrease to 50%: When running other memory-intensive applications')
    
    add_heading(doc, 'Solver Precision', 3)
    add_table(doc, ['Option', 'Accuracy', 'Memory', 'Speed'], [
        ['Single Precision', '~7 digits', 'Lower', 'Faster'],
        ['Double Precision', '~15 digits', '2x', 'Slower'],
    ])
    
    add_placeholder_image(doc, 'Advanced Settings dialog showing RAM slider and precision controls')
    
    doc.add_page_break()
    
    # ==================== PART III ====================
    add_heading(doc, 'PART III: DISPLAY TAB – 3D VISUALIZATION AND ANALYSIS', 1)
    doc.add_paragraph()
    
    # Chapter 15
    add_heading(doc, 'Chapter 15 – Display Tab Overview', 2)
    
    doc.add_paragraph(
        'The Display tab provides an interactive 3D visualization environment powered by PyVista. '
        'This is where you explore, analyze, and export your results.'
    )
    
    add_heading(doc, 'Display Tab Layout', 3)
    add_table(doc, ['Section', 'Location', 'Purpose'], [
        ['Load Visualization File', 'Top', 'Load external CSV for visualization'],
        ['Visualization Controls', 'Below file controls', 'Adjust point size, color scale, deformation'],
        ['Time Point Controls', 'Middle', 'Select time instant, update/save results'],
        ['Animation Controls', 'Below time controls', 'Configure and run animations'],
        ['PyVista 3D Viewer', 'Right side', 'Interactive 3D point cloud display'],
    ])
    
    add_placeholder_image(doc, 'Display tab after solver completion, showing 3D point cloud with color-mapped stress values')
    
    doc.add_page_break()
    
    # Chapter 16
    add_heading(doc, 'Chapter 16 – Visualization Controls (Detailed)', 2)
    
    doc.add_paragraph(
        'The Visualization Controls group provides fine-grained control over the 3D display appearance.'
    )
    
    add_heading(doc, 'Node Point Size', 3)
    doc.add_paragraph('Adjust the rendered size of each node point in the 3D view.')
    add_table(doc, ['Model Size', 'Recommended Point Size'], [
        ['< 10,000 nodes', '5-10'],
        ['10,000 - 100,000 nodes', '3-5'],
        ['> 100,000 nodes', '1-3'],
    ])
    
    add_heading(doc, 'Legend Range (Min/Max)', 3)
    doc.add_paragraph('Set the color scale boundaries for the active scalar field.')
    doc.add_paragraph('• Min Spin Box: Sets the lower bound (blue end of spectrum)')
    doc.add_paragraph('• Max Spin Box: Sets the upper bound (red end of spectrum)')
    
    add_heading(doc, 'Deformation Scale Factor', 3)
    doc.add_paragraph('Amplify or reduce the visual displacement magnitude for animations.')
    doc.add_paragraph('Tip: Keep scale ≤ 5 for realistic-looking visualizations in presentations.')
    
    add_heading(doc, 'Show Absolute Deformations Checkbox', 3)
    add_table(doc, ['Mode', 'When to Use'], [
        ['Unchecked (Relative)', 'Visualizing dynamics, vibration patterns'],
        ['Checked (Absolute)', 'Quantitative analysis, pre-loading effects'],
    ])
    
    add_placeholder_image(doc, 'Visualization Controls group showing all options: point size, min/max legend, deformation scale, absolute deformations checkbox')
    
    doc.add_page_break()
    
    # Chapter 17
    add_heading(doc, 'Chapter 17 – Time Point Controls (Detailed)', 2)
    
    doc.add_paragraph(
        'The Time Point Controls allow you to compute and export results at any specific time instant.'
    )
    
    add_heading(doc, 'Time Selection', 3)
    doc.add_paragraph('Choose the exact time instant for result calculation using the Time (seconds) Spin Box.')
    
    add_heading(doc, 'Update Button', 3)
    doc.add_paragraph('Trigger computation of stress/displacement fields at the selected time:')
    doc.add_paragraph('1. Interpolates modal coordinates to selected time')
    doc.add_paragraph('2. Reconstructs stress tensor field')
    doc.add_paragraph('3. Computes selected output (Von-Mises, Principal, etc.)')
    doc.add_paragraph('4. Updates 3D visualization with new scalar values')
    
    add_heading(doc, 'Save Time Point as CSV', 3)
    doc.add_paragraph('Export the current 3D view data to a CSV file.')
    
    add_heading(doc, 'Export Velocity as Initial Condition in APDL', 3)
    doc.add_paragraph('Generate ANSYS APDL commands for velocity initial conditions.')
    doc.add_paragraph('Appears only when velocity data is available (deformations loaded).')
    
    add_placeholder_image(doc, 'Time Point Controls showing time spinbox, Update button, Save CSV button, and APDL export button')
    
    doc.add_page_break()
    
    # Chapter 18
    add_heading(doc, 'Chapter 18 – Animation Controls (Detailed)', 2)
    
    doc.add_paragraph(
        'The Animation Controls section provides comprehensive options for creating animated visualizations.'
    )
    
    add_heading(doc, 'Time Step Mode', 3)
    add_table(doc, ['Mode', 'Description'], [
        ['Custom Time Step', 'Uniform time intervals you specify'],
        ['Actual Data Time Steps', 'Uses exact times from modal coordinate file'],
    ])
    
    add_heading(doc, 'Playback Interval', 3)
    add_table(doc, ['Interval', 'Frame Rate', 'Use Case'], [
        ['50 ms', '20 fps', 'Smooth presentations'],
        ['100 ms', '10 fps', 'Balanced viewing'],
        ['200 ms', '5 fps', 'Slow-motion analysis'],
    ])
    
    add_heading(doc, 'Playback Controls', 3)
    add_table(doc, ['Button', 'Action'], [
        ['Play', 'Start or resume animation'],
        ['Pause', 'Pause at current frame'],
        ['Stop', 'Stop and reset to beginning'],
    ])
    
    add_heading(doc, 'Save as Video/GIF', 3)
    add_table(doc, ['Format', 'Requirements', 'File Size'], [
        ['MP4', 'ffmpeg installed', 'Smaller'],
        ['GIF', 'Always available', 'Larger'],
    ])
    
    add_placeholder_image(doc, 'Animation Controls showing all options: time step mode, interval, start/end time, play/pause/stop buttons, save button')
    
    doc.add_page_break()
    
    # Chapter 19
    add_heading(doc, 'Chapter 19 – PyVista 3D Viewer Interaction', 2)
    
    doc.add_paragraph(
        'The PyVista 3D Viewer provides an interactive canvas for exploring your results.'
    )
    
    add_heading(doc, 'Mouse Controls', 3)
    add_table(doc, ['Action', 'Result'], [
        ['Left-click + Drag', 'Rotate the view around the focal point'],
        ['Right-click + Drag', 'Pan the view (translate camera)'],
        ['Scroll Wheel', 'Zoom in/out'],
        ['Middle-click + Drag', 'Alternative pan method'],
    ])
    
    add_heading(doc, 'Hover Information', 3)
    doc.add_paragraph('When you hover over a node point:')
    doc.add_paragraph('• A tooltip displays the Node ID and current scalar value')
    doc.add_paragraph('• Useful for quick identification of specific nodes')
    
    add_heading(doc, 'Color Scale (Scalar Bar)', 3)
    doc.add_paragraph('The color scale legend shows:')
    doc.add_paragraph('• Color gradient from minimum (blue) to maximum (red)')
    doc.add_paragraph('• Numerical values at key intervals')
    doc.add_paragraph('• Active scalar field name')
    
    add_placeholder_image(doc, 
        'PyVista 3D viewer showing stress-colored point cloud with:\n'
        '1. Color scale bar on right\n'
        '2. Hover tooltip showing "Node 12345: 234.5 MPa"\n'
        '3. Orientation widget in corner'
    )
    
    doc.add_page_break()
    
    # Chapter 20
    add_heading(doc, 'Chapter 20 – Right-Click Context Menu (Complete Reference)', 2)
    
    doc.add_paragraph(
        'Right-clicking anywhere on the 3D viewer opens a context menu with powerful analysis tools organized into four sections.'
    )
    
    add_heading(doc, 'Section 1: Selection Tools', 3)
    p = doc.add_paragraph()
    p.add_run('Add/Remove Selection Box: ').bold = True
    p.add_run('Create a 3D bounding box to define a region of interest. Drag handles to resize.\n\n')
    p.add_run('Pick Box Center: ').bold = True
    p.add_run('Interactively position the selection box center by clicking in the view.')
    
    add_heading(doc, 'Section 2: Hotspot Analysis', 3)
    p = doc.add_paragraph()
    p.add_run('Find Hotspots (on current view): ').bold = True
    p.add_run('Find nodes with highest scalar values among all currently visible nodes.\n\n')
    p.add_run('Find Hotspots in Selection: ').bold = True
    p.add_run('Find nodes with highest scalar values within the selection box.')
    
    add_heading(doc, 'Section 3: Point-Based Analysis', 3)
    p = doc.add_paragraph()
    p.add_run('Plot Time History for Selected Node: ').bold = True
    p.add_run('Generate a time history plot for a node you select or use the tracked node.')
    
    add_heading(doc, 'Section 4: View Control', 3)
    p = doc.add_paragraph()
    p.add_run('Go To Node: ').bold = True
    p.add_run('Fly the camera to a specific node by entering its ID.\n\n')
    p.add_run('Lock Camera for Animation: ').bold = True
    p.add_run('Keep the camera focused on a tracked node during animation playback.\n\n')
    p.add_run('Reset Camera: ').bold = True
    p.add_run('Return the camera to the default overview position.')
    
    add_placeholder_image(doc, 
        'Context menu showing all four sections:\n'
        'Selection Tools, Hotspot Analysis, Point-Based Analysis, View Control\n'
        'with all menu items visible'
    )
    
    doc.add_page_break()
    
    # Chapter 21
    add_heading(doc, 'Chapter 21 – Hotspot Analysis Workflow', 2)
    
    doc.add_paragraph(
        'Hotspot analysis is a powerful workflow for identifying and investigating critical locations.'
    )
    
    add_heading(doc, 'Complete Workflow', 3)
    doc.add_paragraph('Step 1: Run the solver with desired outputs')
    doc.add_paragraph('Step 2: Adjust visualization (point size, legend range, view angle)')
    doc.add_paragraph('Step 3: Right-click → Find Hotspots (on current view)')
    doc.add_paragraph('Step 4: Enter number of top nodes to find (e.g., 10-20)')
    doc.add_paragraph('Step 5: Review ranked results in Hotspot Dialog')
    doc.add_paragraph('Step 6: Click any row to navigate to that node')
    doc.add_paragraph('Step 7: Right-click → Plot Time History for Selected Node')
    doc.add_paragraph('Step 8: Use Save Time Point as CSV for documentation')
    
    add_heading(doc, 'Hotspot Dialog Features', 3)
    doc.add_paragraph('• Ranked table showing: Rank, NodeID, Value, Coordinates')
    doc.add_paragraph('• Click any row to fly to that node and highlight it')
    doc.add_paragraph('• Dialog stays open for multi-node investigation')
    
    add_placeholder_image(doc, 
        'Complete hotspot workflow montage:\n'
        '1. Full model view  2. Selection box  3. Hotspot dialog\n'
        '4. Time history popup  5. Exported CSV'
    )
    
    doc.add_page_break()
    
    # Chapter 22
    add_heading(doc, 'Chapter 22 – Animation Workflow', 2)
    
    doc.add_paragraph(
        'Creating professional-quality animations requires a systematic approach.'
    )
    
    add_heading(doc, 'Step-by-Step Process', 3)
    doc.add_paragraph('Step 1: Configure Display (point size, legend range, deformation scale)')
    doc.add_paragraph('Step 2: Select Time Step Mode (Custom or Actual)')
    doc.add_paragraph('Step 3: Set playback Interval (ms)')
    doc.add_paragraph('Step 4: Adjust Start and End times')
    doc.add_paragraph('Step 5: Click Play to preview')
    doc.add_paragraph('Step 6: Position camera for best viewing angle')
    doc.add_paragraph('Step 7: Click Save as Video/GIF to export')
    
    add_heading(doc, 'Recommended Settings by Use Case', 3)
    add_table(doc, ['Use Case', 'Time Step', 'Interval', 'Def. Scale'], [
        ['Quick preview', 'Every 10th', '100 ms', '5'],
        ['Presentation', '0.01s custom', '50 ms', '3'],
        ['High-detail', '0.001s custom', '100 ms', '2'],
        ['Slow-motion', 'Every 1st', '200 ms', '1'],
    ])
    
    add_placeholder_image(doc, 'Animation export sequence showing controls, 3D view with frame, save dialog, success message')
    
    doc.add_page_break()
    
    # ==================== PART IV ====================
    add_heading(doc, 'PART IV: EXPORT AND DATA MANAGEMENT', 1)
    doc.add_paragraph()
    
    # Chapter 23
    add_heading(doc, 'Chapter 23 – Exporting Results to CSV', 2)
    
    doc.add_paragraph(
        'MARS provides multiple ways to export computational results for further processing or documentation.'
    )
    
    add_heading(doc, 'Automatic Exports After Solving', 3)
    add_table(doc, ['Output Type', 'Filename Pattern'], [
        ['Von-Mises Stress', 'von_mises.csv, time_of_max_von_mises.csv'],
        ['Max Principal', 'max_principal.csv, time_of_max_principal.csv'],
        ['Min Principal', 'min_principal.csv, time_of_min_principal.csv'],
        ['Deformation', 'deformation.csv, time_of_max_deformation.csv'],
        ['Velocity', 'velocity.csv, time_of_max_velocity.csv'],
        ['Acceleration', 'acceleration.csv, time_of_max_acceleration.csv'],
    ])
    
    add_heading(doc, 'Manual Time Point Export', 3)
    doc.add_paragraph('1. Go to Display tab')
    doc.add_paragraph('2. Set desired time in Time Point Controls')
    doc.add_paragraph('3. Click Update')
    doc.add_paragraph('4. Click Save Time Point as CSV')
    doc.add_paragraph('5. Choose filename and location')
    
    add_placeholder_image(doc, 'File explorer showing exported CSV files in project directory')
    
    doc.add_page_break()
    
    # Chapter 24
    add_heading(doc, 'Chapter 24 – APDL Initial Condition Export', 2)
    
    doc.add_paragraph(
        'The APDL Initial Condition export allows you to restart ANSYS transient analyses from any time point computed in MARS.'
    )
    
    add_heading(doc, 'Requirements', 3)
    doc.add_paragraph('• Deformation file must be loaded')
    doc.add_paragraph('• Solver must complete successfully')
    doc.add_paragraph('• Time point must be computed with velocity data')
    
    add_heading(doc, 'Export Procedure', 3)
    doc.add_paragraph('1. Go to Display tab')
    doc.add_paragraph('2. Set the desired time in Time Point Controls')
    doc.add_paragraph('3. Click Update to compute velocity')
    doc.add_paragraph('4. Click Export Velocity as Initial Condition in APDL')
    doc.add_paragraph('5. Choose filename (default: initial_conditions.inp)')
    
    add_heading(doc, 'Using in ANSYS', 3)
    doc.add_paragraph('1. Copy the .inp file to your ANSYS working directory')
    doc.add_paragraph('2. Before SOLVE, use: *USE,initial_conditions.inp')
    doc.add_paragraph('3. Run transient analysis with IC applied')
    
    add_placeholder_image(doc, 'APDL export dialog and snippet of generated .inp file content')
    
    doc.add_page_break()
    
    # ==================== PART V ====================
    add_heading(doc, 'PART V: TROUBLESHOOTING AND REFERENCE', 1)
    doc.add_paragraph()
    
    # Chapter 25
    add_heading(doc, 'Chapter 25 – Troubleshooting Guide', 2)
    
    add_heading(doc, 'File Loading Issues', 3)
    add_table(doc, ['Symptom', 'Cause', 'Solution'], [
        ['Invalid MCF file', 'Missing Time header', 'Ensure first column is "Time"'],
        ['Required column not found', 'Wrong column naming', 'Check stress columns match sx_1, sy_1, etc.'],
        ['File won\'t load', 'File encoding issue', 'Re-save as UTF-8 CSV'],
    ])
    
    add_heading(doc, 'Solver Issues', 3)
    add_table(doc, ['Symptom', 'Cause', 'Solution'], [
        ['SOLVE button disabled', 'Missing input files', 'Load both .mcf and stress .csv'],
        ['Out of memory error', 'Exceeded RAM', 'Increase RAM allocation in Settings'],
        ['Very slow performance', 'Using double precision', 'Switch to single precision'],
    ])
    
    add_heading(doc, 'Display Tab Issues', 3)
    add_table(doc, ['Symptom', 'Cause', 'Solution'], [
        ['Blank 3D view', 'No data loaded', 'Run solver or load visualization CSV'],
        ['Animation won\'t play', 'No deformations', 'Load deformation file and re-solve'],
        ['MP4 export fails', 'ffmpeg not installed', 'Install ffmpeg or use GIF'],
    ])
    
    add_placeholder_image(doc, 'Troubleshooting flowchart for common issues')
    
    doc.add_page_break()
    
    # Chapter 26
    add_heading(doc, 'Chapter 26 – File Format Reference', 2)
    
    add_heading(doc, 'Modal Coordinate File (.mcf)', 3)
    doc.add_paragraph('Time,Mode1,Mode2,Mode3,...,ModeN')
    doc.add_paragraph('0.0000,1.23e-4,2.45e-5,3.67e-6,...')
    
    add_heading(doc, 'Modal Stress File (.csv)', 3)
    doc.add_paragraph('Required: NodeID, sx_n, sy_n, sz_n, sxy_n, syz_n, sxz_n')
    doc.add_paragraph('Optional: X, Y, Z coordinates')
    
    add_heading(doc, 'Modal Deformation File (.csv)', 3)
    doc.add_paragraph('Required: NodeID, ux_n, uy_n, uz_n')
    
    add_heading(doc, 'Steady-State Stress File (.txt)', 3)
    doc.add_paragraph('Tab-delimited: NodeID, SX, SY, SZ, SXY, SYZ, SXZ')
    
    add_heading(doc, 'Temperature Field File (.csv)', 3)
    doc.add_paragraph('Required: NodeID, Temperature')
    
    doc.add_page_break()
    
    # Chapter 27
    add_heading(doc, 'Chapter 27 – Keyboard and Mouse Reference', 2)
    
    add_heading(doc, 'Mouse Controls (PyVista 3D Viewer)', 3)
    add_table(doc, ['Action', 'Mouse Operation'], [
        ['Rotate view', 'Left-click + drag'],
        ['Pan view', 'Right-click + drag'],
        ['Zoom', 'Scroll wheel'],
        ['Show tooltip', 'Hover over node'],
        ['Context menu', 'Right-click (no drag)'],
    ])
    
    add_heading(doc, 'General UI Controls', 3)
    add_table(doc, ['Action', 'Control'], [
        ['Switch tabs', 'Click tab button'],
        ['Enter value', 'Type in field + Enter'],
        ['Toggle checkbox', 'Click checkbox'],
    ])
    
    doc.add_page_break()
    
    # Chapter 28
    add_heading(doc, 'Chapter 28 – FAQs', 2)
    
    faqs = [
        ('Q: Which outputs require the deformation file?',
         'A: Deformation, Velocity, and Acceleration outputs require the modal deformation file.'),
        ('Q: Can I compare results with the same color scale?',
         'A: Yes. Manually set Legend Range min/max to fixed values across different analyses.'),
        ('Q: How do I focus on a single node?',
         'A: Right-click → Go To Node, enter the Node ID, then optionally Lock Camera for Animation.'),
        ('Q: When should I use plasticity correction?',
         'A: When elastic stress at notches, holes, or fillets exceeds the material yield stress.'),
        ('Q: Which plasticity method should I choose?',
         'A: Start with Neuber (faster). Use Glinka for more conservative results.'),
        ('Q: How can I speed up large analyses?',
         'A: Go to Settings → Advanced. Increase RAM, use Single precision, or reduce output scope.'),
        ('Q: What does "Skip first n modes" do?',
         'A: Excludes the first n modes from reconstruction. Skip rigid-body modes (typically 6).'),
        ('Q: How do I track a node during animation?',
         'A: Use Go To Node, then enable Lock Camera for Animation from the context menu.'),
    ]
    
    for q, a in faqs:
        p = doc.add_paragraph()
        p.add_run(q).bold = True
        doc.add_paragraph(a)
        doc.add_paragraph()
    
    doc.add_page_break()
    
    # Chapter 29
    add_heading(doc, 'Chapter 29 – Getting Help', 2)
    
    add_heading(doc, 'Before Submitting a Support Request', 3)
    doc.add_paragraph('Gather this information:')
    doc.add_paragraph('1. Error messages from the Console')
    doc.add_paragraph('2. Steps to reproduce the issue')
    doc.add_paragraph('3. Input files (if you can share them)')
    doc.add_paragraph('4. Screenshots of the state when the error occurred')
    
    add_heading(doc, 'Diagnostic Information', 3)
    doc.add_paragraph(
        'MARS logs helpful information to the Console. When reporting issues, include '
        'the complete console output, contents of any error dialogs, and MARS version information.'
    )
    
    add_heading(doc, 'Contact', 3)
    doc.add_paragraph('For assistance with MARS, contact your designated maintainer or system administrator.')
    
    doc.add_paragraph()
    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run('— End of MARS User Manual —').italic = True
    
    # Save the document
    doc.save(OUTPUT_PATH)
    print(f"User manual saved to: {OUTPUT_PATH}")


if __name__ == '__main__':
    create_manual()
