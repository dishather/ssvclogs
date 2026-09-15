# ssvclogs
Plot graphs for SSVC0059 V2 logs (any version)

## Read SSVC0059 V2 logs and plot neat graphs

SSVC0059 is a specialized controller for alcohol rectification. Its V2 version
can be upgraded with different firmware. Its logs can be plotted and analyzed.

Usage: makeplot.py <LOGFILE.CSV>

The graph will be saved to <LOGFILE.PNG>


## Graphs description

This script does almost the same as the official "log analyzer" in SSVC0059
chat in Telegram.

The main differences are:

- All stages are shown, not only the "hearts" stage.
- Processes logs from any firmware version from the PRO series (both 2.2.XX
  and 2.3.XX). Older firmware logs lack some parameters (e.g., predecrement), so
  the graphs may have limited use.


## Common grpah sections

Different parts have different background colors. Sections correspond to
different stages in controller operation.

White background: normal data ("hearts/body" section).

Light blue background: "heads" section ("foreshots" for 2.3.XX firmware
versions).

Light green background: "tails" section (or "low heads" for 2.3.XX firmware
versions).

Light red background: waiting for the tempetature to return to the baseline
("stop").


## ABV graph

Shows the ABV of the low spirits in the pot.


## Volume graph

Shows the volume of the liquids collected, in liters. For older firmware
versions, shows volumes in "arbitrary units".


### Speed graph

Shows speed in milliliters per hour (as configured on the controller).
For older firmware versions, shows speed in percentages of the time the
valve was open.


### Temperature graph

Shows the TD1 temperature (i.e., the temperature in the column). The graph's
main aim os to show subtle temperature variations during the "body" stage, so
extreme temperature variations during "heads" and "tails" stages may be
omitted.

The graph also shows:

- Baseline temperature as remembered by the controller (green line).
- Predecrement temperature if saved in the log (orange line).
- Hysteresis temperature if saved in the log (red line).


### TD2 Graph (pot temperature)

Shows TD2 temperature graph (temperature of low wines in the pot).

The graph also shows:

- 92C line (red dotted line).
- Finish line (green dotted line).
- Time when TD2 crossed 92C (cyan vertical line).
- Time when the first predecrement was hit (dark green dotted vertical line).
- Point where TD2 reached 94C.

### Pressure graph

Shows atmospheric presssure during the rectification session, in mm Hg. The
controller automatically adjusts all the temperatures to the basic 780 mm Hg
atmospheric pressure.
