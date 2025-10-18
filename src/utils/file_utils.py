"""
File utility functions for the MSUP Smart Solver.

This module contains helper functions for file manipulation and processing.
"""


def unwrap_mcf_file(input_file, output_file):
    """
    Unwraps a Modal Coordinate File (MCF) that has wrapped data lines.
    
    After the header line (the one starting with "Number of Modes"), some records
    are wrapped across multiple lines. Additionally, there is a column header line
    (e.g. "Time          Coordinates...") in the data block that should remain
    separate.
    
    Algorithm:
    1. Keeps all lines up to and including the line that starts (after stripping)
       with "Number of Modes".
    2. For the remaining lines, if a line (after stripping) contains both "Time"
       and "Coordinates", it is treated as a header line and is preserved as its
       own record.
    3. For other lines, the minimum indentation among them is determined (the base
       indent). Lines with exactly that indentation start new records, while lines
       with extra indentation are treated as continuations (wrapped lines) and
       appended to the previous record.
    
    Args:
        input_file: Path to the input MCF file with wrapped lines.
        output_file: Path to save the unwrapped output file.
    
    Returns:
        list: List of unwrapped lines.
    """
    # Read all lines
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    # Separate header (everything up to and including "Number of Modes")
    header_end = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("Number of Modes"):
            header_end = i
            break
    
    if header_end is None:
        header_lines = []
        data_lines = lines
    else:
        header_lines = lines[:header_end + 1]
        data_lines = lines[header_end + 1:]
    
    # For base indentation calculation, skip header lines with "Time" and "Coordinates"
    data_non_header = []
    for line in data_lines:
        stripped = line.strip()
        if stripped and ("Time" in stripped and "Coordinates" in stripped):
            continue  # skip header lines for indent calculation
        if stripped:
            data_non_header.append(line)
    
    base_indent = None
    for line in data_non_header:
        indent = len(line) - len(line.lstrip(' '))
        if base_indent is None or indent < base_indent:
            base_indent = indent
    if base_indent is None:
        base_indent = 0
    
    # Process data lines
    unwrapped_data = []
    current_line = ""
    for line in data_lines:
        stripped = line.strip()
        if not stripped:
            continue  # skip empty lines
        
        # If this line is the special header (e.g., "Time          Coordinates...")
        if "Time" in stripped and "Coordinates" in stripped:
            if current_line:
                unwrapped_data.append(current_line)
                current_line = ""
            unwrapped_data.append(stripped)
            continue
        
        # Determine indentation of the current line
        indent = len(line) - len(line.lstrip(' '))
        if indent == base_indent:
            # New record
            if current_line:
                unwrapped_data.append(current_line)
            current_line = stripped
        else:
            # Wrapped (continuation) line
            current_line = current_line.rstrip('\n') + " " + stripped
    
    if current_line:
        unwrapped_data.append(current_line)
    
    # Combine header and unwrapped data
    final_lines = [h.rstrip('\n') for h in header_lines] + unwrapped_data
    
    # Write final result to output file
    with open(output_file, 'w') as f:
        for line in final_lines:
            f.write(line + "\n")
    
    return final_lines

