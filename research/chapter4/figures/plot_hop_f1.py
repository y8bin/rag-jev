"""Figures4papers scientific-figure-making style; existing A2 data only.

Local implementation of its API conventions, as the upstream skill specifies.
Render a provisional single-column figure; no uncertainty or subgroup tests.
Run from repository root: .venv/bin/python research/chapter4/figures/plot_hop_f1.py
"""
from dataclasses import dataclass
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/chapter4-matplotlib")
os.environ.setdefault("XDG_CACHE_HOME", "/private/tmp/chapter4-cache")
Path(os.environ["XDG_CACHE_HOME"]).mkdir(parents=True, exist_ok=True)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path("research/chapter4/figures")
SOURCE = Path("results/koblex-reproduction-v1/chapter4-prep-v1/A2/hop-f1-figure-data.csv")
PALETTE = {"blue_main": "#0F4D92", "red_strong": "#B64342", "neutral": "#CFCECE"}


@dataclass(frozen=True)
class FigureStyle:
    font_size: int = 18
    axes_linewidth: float = 2
    use_tex: bool = False
    font_family: tuple[str, ...] = ("DejaVu Sans", "Helvetica", "Arial", "sans-serif")


def apply_publication_style(style=FigureStyle()):
    plt.rcParams.update({"font.family": list(style.font_family), "font.size": style.font_size,
                         "axes.linewidth": style.axes_linewidth, "axes.spines.top": False,
                         "axes.spines.right": False, "legend.frameon": False,
                         "text.usetex": style.use_tex, "pdf.fonttype": 42, "ps.fonttype": 42,
                         "svg.fonttype": "none", "axes.unicode_minus": False})


def make_trend(ax, x, y_series, labels, colors, ylabel=None, xlabel=None, show_shadow=False):
    assert show_shadow is False, "No subgroup CI was computed; do not invent a band"
    x = np.asarray(x)
    assert x.ndim == 1 and len(y_series) == len(labels) == len(colors)
    for values, label, color, marker, linestyle in zip(y_series, labels, colors, ("s", "o"), ("--", "-")):
        values = np.asarray(values, dtype=float)
        assert values.ndim == 1 and values.shape == x.shape and np.isfinite(values).all()
        ax.plot(x, values, label=label, color=color, marker=marker, linestyle=linestyle,
                linewidth=2.5, markersize=8)
    ax.set_ylabel(ylabel)
    if xlabel:
        ax.set_xlabel(xlabel)


def finalize_figure(fig, out_path, formats=("pdf", "svg", "png"), dpi=600, close=True, pad=.05):
    fig.tight_layout(pad=1)
    saved = []
    for fmt in formats:
        assert fmt in ("pdf", "svg", "png")
        target = Path(out_path).with_suffix("." + fmt)
        target.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(target, dpi=dpi, bbox_inches="tight", pad_inches=pad, facecolor="white",
                    metadata={"Creator": "Matplotlib; figures4papers scientific-figure-making conventions"} if fmt == "pdf" else None)
        saved.append(target)
    if close:
        plt.close(fig)
    return saved


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    with SOURCE.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 6
    values = {arm: [next(r for r in rows if r["arm"] == arm and r["subgroup"] == f"hop_{h}") for h in (1, 2, 3)]
              for arm in ("parser_ce_fixed", "parser_jev_fixed")}
    assert [int(r["n"]) for r in values["parser_ce_fixed"]] == [57, 127, 42]
    ys = [[float(r["raw_mean"]) * 100 for r in values[a]] for a in values]
    apply_publication_style()
    # Canvas halves to about 85 mm in the current two-column draft: base 18 pt -> ~9 pt.
    fig, ax = plt.subplots(figsize=(6.8, 3.5))
    make_trend(ax, [1, 2, 3], ys, ["CE", "Jev"],
               [PALETTE["red_strong"], PALETTE["blue_main"]], ylabel="Evidence F1 (0-100)")
    ax.set_xlim(.73, 3.27)
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_xticks([1, 2, 3], ["1-hop\n(n=57)", "2-hop\n(n=127)", "3-hop\n(n=42)"])
    ax.tick_params(labelsize=17, width=1.5, length=4)
    for j, values_at_hop in enumerate(zip(*ys)):
        for k, value in enumerate(values_at_hop):
            above = (j == 0 and k == 0) or (j > 0 and k == 1)
            ax.annotate(f"{value:.2f}", (j + 1, value), xytext=(0, 9 if above else -11),
                        textcoords="offset points", ha="center", va="bottom" if above else "top",
                        fontsize=16, color=PALETTE["red_strong"] if k == 0 else PALETTE["blue_main"])
    ax.legend(loc="upper right", ncol=2, fontsize=16, columnspacing=1.2, handlelength=1.6)
    saved = finalize_figure(fig, ROOT / "hop_f1")
    shutil.copyfile(SOURCE, ROOT / "hop_f1.csv")
    refs = ROOT / "skill-references"
    provenance = {
        "data_source": str(SOURCE), "data_source_sha256": sha(SOURCE), "copied_data_sha256": sha(ROOT / "hop_f1.csv"),
        "skill": "scientific-figure-making", "repository": "https://github.com/ChenLiu-1996/figures4papers",
        "commit": "b709de17da7e8f9a72e51a5de5bced924a01eeab",
        "implementation": "local API implementation, per pinned tutorials/API; no tracked shared upstream Python module",
        "skill_references": {str(p): sha(p) for p in sorted(refs.glob("*.md"))},
        "plot_script_sha256": sha(__file__), "matplotlib": matplotlib.__version__, "numpy": np.__version__,
        "layout": "provisional 85 mm single column; 6.8x3.5 in source scaled to column width",
        "style": "18 pt base font; blue Jev / red CE; circle/solid versus square/dashed; top/right spines off; frameless legend; editable vector text",
        "uncertainty": "descriptive point estimates; no CI, significance or interaction inference added",
        "outputs": {str(p): sha(p) for p in saved},
    }
    (ROOT / "hop_f1.provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")
    print("Created " + ", ".join(str(p) for p in saved))


if __name__ == "__main__":
    main()
