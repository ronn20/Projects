#!/usr/bin/env python
from __future__ import print_function
import yt
import argparse 
import matplotlib
import glob
import os
import imageio.v2 as imageio
matplotlib.rcParams['font.family'] = 'sans-serif'
matplotlib.rcParams['font.sans-serif'] = ['DejaVu Sans']
matplotlib.rcParams['text.usetex'] = False

parser = argparse.ArgumentParser(
    description="Batch slice and plot FLASH 2D (r–z) files."
)
#parser.add_argument("dataset",nargs="+", metavar="dataset", help="FLASH HDF5 file")
parser.add_argument("pattern",
    help="Glob pattern to match your HDF5 files, e.g. results/hdef_hdf5_plt_cnt_*")
parser.add_argument("-field", "--field", default="phqn",
    help="Scalar FLASH field to plot (e.g. 'phqn', 'dens')")
parser.add_argument("-denscont", "--densitycontour", type=float,
    help="Density value for single contour overlay")
parser.add_argument("-denscontcolor", "--densitycontourcolor", default="0099FF",
    help="Hex color for density contour")
parser.add_argument("-denscontwidth", "--densitycontwidth", type=float, default=1.0,
    help="Line width for density contour")
parser.add_argument("-log", "--takelog", action="store_true",
    help="Plot log10 of the field")
parser.add_argument("-rd", "--r_down", type=float,
    help="r lower bound (km)")
parser.add_argument("-ru", "--r_up",   type=float,
    help="r upper bound (km)")
parser.add_argument("-zd", "--z_down", type=float,
    help="z lower bound (km)")
parser.add_argument("-zu", "--z_up",   type=float,
    help="z upper bound (km)")
parser.add_argument("-dpi", "--dpi", type=int, default=300,
    help="Output DPI")
parser.add_argument("-o", "--output", default="slice.png",
    help="Output filename (png/eps)")
parser.add_argument(
    "--outdir", type=str,
    help=("If set, creates this directory and writes one PNG per input" 
    "into it, named <basename>.png"))
parser.add_argument("--zoom-start", type=float, default=200.0,
    help="Initial zoom factor")
parser.add_argument("--zoom-end", type=float, default=25,
    help="Final zoom factor")
args = parser.parse_args()

os.makedirs(args.outdir, exist_ok=True)

# Load in dataset via pattern. # … snip parser, imports, glob, etc. …

plots = sorted(glob.glob(args.pattern))
N = len(plots)
if N == 0:
    raise RuntimeError("No files matched: " + args.pattern)

# Load the first dataset just to get the global domain
ds0 = yt.load(plots[0])
le = ds0.domain_left_edge.to("cm").value   # [rmin, zmin, thetamin]
ri = ds0.domain_right_edge.to("cm").value  # [rmax, zmax, thetamax]

rmin_cm, rmax_cm = le[0], ri[0]
zmin_cm, zmax_cm = le[1], ri[1]

full_w_r = rmax_cm - rmin_cm
full_w_z = zmax_cm - zmin_cm

for i, fn in enumerate(plots):
    ds = yt.load(fn)

    # exponentially interpolate zoom
    zoom = args.zoom_start * (args.zoom_end/args.zoom_start)**(i/(N-1))

    # compute per-frame widths
    w_r = full_w_r / zoom
    w_z = full_w_z / zoom

    r_ctr = rmin_cm + 0.5*w_r
    z_ctr = 0.5*(zmin_cm + zmax_cm)

    slc = yt.SlicePlot(ds, "theta", ("flash", args.field))
    slc.set_center([r_ctr,z_ctr])
    slc.set_width((w_r, w_z))    # <-- directly set the slice width

    slc.set_cmap(("flash", args.field), "jet")
    slc.set_log(("flash", args.field), args.takelog)
    slc.annotate_timestamp(time_unit="s", corner="upper_right")
    if args.densitycontour is not None:
        slc.annotate_contour(
            ("flash","density"), ncontours=1,
            clim=(args.densitycontour, args.densitycontour),
            colors=[f"#{args.densitycontourcolor}"],
            linewidths=args.densitycontwidth
        )
    slc.set_axes_unit("km")

    base = os.path.splitext(os.path.basename(fn))[0]
    outname = os.path.join(args.outdir, base + ".png")
    slc.save(outname, mpl_kwargs={"dpi": args.dpi})
    print(f"  → Wrote {outname!r} (frame {i+1} of {N})")


# 11) Put all the .png files into an animation!
images = []
image_files = sorted(glob.glob(os.path.join(args.outdir,"hdef_hdf5_plt_cnt_*.png")))
for filename in image_files:
    images.append(imageio.imread(filename))
imageio.mimsave('Sne_deton_zoomcontrol_YT_SlicePlot_1.7s.mp4', images, fps=10)
print("Animation saved")
