"""Build a solid blade (STEP) from a BladeGen/TurboGrid profile.curve file.

Usage (in the Simly venv, which already has gmsh):
    python blade_step.py profile.curve blade.step

The curve file holds one closed airfoil section per span station, from hub to
shroud, as "x y z" rows (any units: the STEP keeps them; Rotor 37 is in cm).
Sections are separated by lines starting with '#' or by blank lines. The blade
is lofted through the sections and written as one solid, in the same
coordinates as the CFD mesh, so CFX pressures map straight onto it.
"""

import sys

import gmsh
import numpy as np


def read_sections(path):
    sections, current = [], []
    for line in open(path, encoding="utf-8", errors="ignore"):
        s = line.strip()
        parts = s.replace(",", " ").split()
        try:
            row = [float(v) for v in parts[:3]] if len(parts) >= 3 else None
        except ValueError:
            row = None
        if row is None:  # comment, header or blank line: closes a section
            if len(current) >= 4:
                sections.append(np.array(current))
            current = []
            continue
        current.append(row)
    if len(current) >= 4:
        sections.append(np.array(current))
    return sections


def clean(points):
    """Drop repeated points and the closing duplicate."""
    keep = [points[0]]
    for p in points[1:]:
        if np.linalg.norm(p - keep[-1]) > 1e-9:
            keep.append(p)
    pts = np.array(keep)
    if np.linalg.norm(pts[0] - pts[-1]) < 1e-6 * np.ptp(pts, axis=0).max():
        pts = pts[:-1]
    return pts


def main(src, dst):
    sections = [clean(s) for s in read_sections(src)]
    if len(sections) < 2:
        sys.exit(f"found {len(sections)} section(s) in {src}; need at least 2")
    print(f"{len(sections)} sections, {[len(s) for s in sections]} points")
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("blade")
    occ = gmsh.model.occ
    wires = []
    for pts in sections:
        tags = [occ.addPoint(*p) for p in pts]
        # periodic spline through every point, closed at the first one
        curve = occ.addSpline(tags + [tags[0]])
        wires.append(occ.addWire([curve]))
    out = occ.addThruSections(wires, makeSolid=True, makeRuled=False)
    occ.synchronize()
    vols = [t for d, t in out if d == 3]
    if len(vols) != 1:
        sys.exit("the loft did not give one solid; check the section order in the file")
    volume = occ.getMass(3, vols[0])
    lo = gmsh.model.getBoundingBox(3, vols[0])
    gmsh.write(dst)
    gmsh.finalize()
    print(f"wrote {dst}: volume {volume:.4g} (file units^3), "
          f"bbox {np.round(lo[:3], 3).tolist()} to {np.round(lo[3:], 3).tolist()}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
