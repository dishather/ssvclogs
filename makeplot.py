#!/usr/bin/python3

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import sys
import math
from pathlib import Path

def load_logfile( filename ):
    with open( filename, mode='r', encoding='cp1251') as file:
        lines = [line.strip() for line in file]

    # prepate result
    res = {
        'info': {
            'version': 'неизвестно',
            'hysteresis': 0,
            'predecrement': 0,
            'valve1': 100,
            'valve2': 100,
            'valve3': 100,
        },

        "stage": [],
        "time": [],
        "tset": [],
        "vopen": [],
        "vperiod": [],
        "pressure": [],
        "td1": [],
        "td2": [],
        "guo": [],
        "uo": [],
        "suo": [],
        "abv": [],
        "isstop": [],
        "predeccnt": []
    }

    for line in lines:
        data = line.split(';')

        # first process header if it is present
        if len(data) == 2:
            match data[0]:
                case "V":
                    res["info"]["version"] = data[1]
                case "H":
                    res["info"]["hysteresis"] = float(data[1].replace(',', '.'))
                case "PRE":
                    if data[1][0] == '0': # may be "off"
                        res["info"]["predecrement"] = float(data[1].replace(',', '.'))
                case "V1":
                    res["info"]["valve1"] = float(data[1].replace(',', '.'))
                case "V2":
                    res["info"]["valve2"] = float(data[1].replace(',', '.'))
                case "V3":
                    res["info"]["valve3"] = float(data[1].replace(',', '.'))

        # otherwise process data itself
        if len(data) > 16:
            if data[0].isdigit():
                res["stage"].append(int(data[0]))
                res["time"].append(data[1])
                res["tset"].append(float(data[2].replace(',', '.')))
                res["vopen"].append(float(data[3].replace(',', '.')))
                res["vperiod"].append(int(data[4]))
                res["pressure"].append(float(data[6].replace(',', '.')))
                res["td1"].append(float(data[10].replace(',', '.')))
                res["td2"].append(float(data[11].replace(',', '.')))
                res["guo"].append(int(data[12]))
                res["uo"].append(int(data[13]))
                res["suo"].append(int(data[14]))
                res["abv"].append(float(data[15].replace(',', '.')))
                res["isstop"].append(int(data[16]))
                if res["info"]["predecrement"] > 0:
                    res["predeccnt"].append(int(data[18]))
                else:
                    res["predeccnt"].append(0)

    return res

# draw basic plot
def draw_plot( ax, config, d, label, annotation ):
    ax.set_xticks( config["ticks"], config["labels"] )
    ax.grid()
    ax.set( ylabel = label )
    cross92label = "ТД2 пересёк 92С" if config["addLegends"] else "";
    predeclabel = "Первый предекремент" if config["addLegends"] else "";

    if config["cross92"] > 0:
        ax.axvline( config["cross92"], color="c", label=cross92label )
    if config["firstPredec"] > 0:
        ax.axvline( config["firstPredec"], color="g", linestyle="--", label=predeclabel )
    if len(config["headsSpan"]) == 2:
        ax.axvspan(config["headsSpan"][0], config["headsSpan"][1], color = ("b", 0.1) )
    if len(config["subHeadsSpan"]) == 2:
        ax.axvspan(config["subHeadsSpan"][0], config["subHeadsSpan"][1], color = ("g", 0.1) )
    for s in config["stopsSpans"]:
        ax.axvspan(s[0], s[1], color = ("r", 0.1) )
    if len(d) > 0:
        if isinstance(d[0], (int, float)):
            ax.plot( xs, d, color = config["plotColor"], label = config["plotlabel"] )
            ax.annotate( annotation.format( d[-1]), xy=(xs[-1], d[-1]))
        else:
            cnt = 0
            for dp in d:
                ax.plot( xs, dp, label = config["plotlabels"][cnt] )
                ax.annotate( annotation.format( dp[-1]), xy=(xs[-1], dp[-1]))
                cnt += 1

# converts time string to seconds (takes 2 possible formats into account)
def toSeconds( time ):
    t = time.split(":")
    if len(t) == 2:
        h, m = map(int, t)
        return h * 3600 + m * 60
    else:
        h, m, s = map(int, t)
        return h * 3600 + m * 60 + s

# Data
data = load_logfile(sys.argv[1])

isNewVersion = (data["info"]["hysteresis"] > 0)
is23Version = data["info"]["version"].startswith("2.3.")

# prepare output filename
outfile = filename = Path(sys.argv[1]).stem + '.PNG'

# time ticks converted to seconds
xs = [toSeconds(t) for t in data["time"]]

# when td2 crosses 92 degrees C
td2crosses92 = 0
firstPredec = 0
stopsSpans = [] # list of from..to spans
stopStart = -1 # auxiliary
stageLastTick = [-1, -1, -1, -1]
ticks = []
labels = []
divider = 60 # used for labels
if len(xs) / divider < 10:
    divider /= 2
if len(xs) / divider < 10:
    divider /= 2
if len(xs) / divider < 10:
    divider = 10
if len(xs) / divider < 10:
    divider /= 2

for t in range(len(xs)):
    if data["td2"][t] >= 92.0 and td2crosses92 == 0:
        td2crosses92 = xs[t]
    stageLastTick[data["stage"][t]] = xs[t]

    if data["isstop"][t] == 1:
        if stopStart < 0:
            stopStart = xs[t]
    else:
        if stopStart >= 0:
            stopsSpans.append([stopStart, xs[t - 1]])
            stopStart = -1
    # fill ticks and labels
    time = data["time"][t].split(":")
    minutes = int(time[1])
    if minutes % divider == 0:
        ticks.append(xs[t])
        labels.append(data["time"][t])
    # seek for the first predecrement
    if firstPredec == 0 and int(data["predeccnt"][t]) > 0:
        firstPredec = xs[t]

# A bit of heuristics. For older firmware, we don't actually
# know if it is a usual Pro version (2.2.X) or Pro.3H (2.3.X).
# But in fact, for 2.2.X versions, the last third stage is not
# usable at all. OTOH, for versions 2.3.X it is where the actual
# work is done. So, we compare the time spent for both stages,
# and if stage 3 is longer than stage 2 - it's Pro.3H version.
if not isNewVersion:
    stageLen = [0, 0, 0, 0]
    lastPos = 0
    for i in range(4):
        if stageLastTick[i] >= lastPos:
            stageLen[i] = stageLastTick[i] - lastPos
            lastPos = stageLastTick[i]
    if stageLen[3] > stageLen[2]:
        is23Version = True
        data["info"]["version"] += " (предположительно серии Pro.3H)"


headsSpan = [] # from..to in X ticks
subHeadsSpan = [] # only present in 2.3.x versions
tailsSpan = [] # only in 2.2.X

if stageLastTick[1] >= 0:
    headsSpan.append(0);
    headsSpan.append(stageLastTick[1]);

if stageLastTick[2] >= 0 and is23Version:
    subHeadsSpan.append(stageLastTick[1] + 1);
    subHeadsSpan.append(stageLastTick[2]);

if stageLastTick[3] >= 0 and not is23Version:
    tailsSpan.append(stageLastTick[2] + 1);
    tailsSpan.append(stageLastTick[3]);

# prepare config
config = {
        "ticks": ticks,
        "labels": [],
        "stopsSpans": stopsSpans,
        "cross92": td2crosses92,
        "firstPredec": firstPredec,
        "headsSpan": headsSpan,
        "subHeadsSpan": subHeadsSpan if is23Version else tailsSpan,
        "addLegends": False,
        "plotColor": None,
        "plotlabel": ""
    }

# Alright, start plotting.
# Plot configuration
plt.rcParams['lines.linewidth'] = 1
plt.rcParams['font.size'] = 6
plt.rcParams['legend.framealpha'] = 0.6

fig, ax = plt.subplots(6, 1)
fig.set_size_inches(10, 10)
fig.suptitle( "Версия прошивки: {}".format( data["info"]["version"]) )
fig.set_layout_engine( 'constrained' )

# ABV GRAPH
draw_plot( ax[0], config, data["abv"], "Содерж. спирта, %об", "{:03.1f}%" )

# VOLUMES GRAPH
volHeads = [ (sec * data["info"]["valve1"]) / 3600000 for sec in data["guo"]]
volBody = [ (sec * data["info"]["valve2"]) / 3600000 for sec in data["uo"]]
volTails = [ (sec * data["info"]["valve3"]) / 3600000 for sec in data["suo"]]

config["plotlabels"] = ["Головы", "Тело", "Хвосты"]
if is23Version:
    config["plotlabels"][2] = "Подголовники";

p = [volHeads, volBody]

if int(data["suo"][-1]) > 0:
    p.append(volTails)

draw_plot( ax[1], config, p,
    "Объём, {}".format( "л" if isNewVersion else "усл.ед."),
    "{{:.3f}} {}".format( "л" if isNewVersion else "ед.") )
ax[1].legend( loc='upper left' )

# SPEED GRAPH
valveMapping = ['', "valve1", "valve2", "valve3"] # which valve is active at which stage
if is23Version:
    valveMapping = ['', "valve1", "valve3", "valve2"]

speeds = [ (data["info"][valveMapping[data["stage"][t]]] * data["vopen"][t])/data["vperiod"][t]
    if not data["isstop"][t] > 0 else 0 for t in range(len(xs))]
draw_plot( ax[2], config, speeds,
    "Скорость, {}".format( "мл/ч" if isNewVersion else "%"),
    "{{:.1f}} {}".format( "мл/ч" if isNewVersion else "%") )

# TD1 GRAPH
# since we are interested in temperatures during the main stage, replace everything too high/low with NaN
bodyMinMax = [500, 0]
# tset = 0
stage = 3 if is23Version else 2;
for t in range(len(xs)):
    if data["stage"][t] == stage:
        if data["td1"][t] < bodyMinMax[0]:
            bodyMinMax[0] = data["td1"][t]
        if data["td1"][t] > bodyMinMax[1]:
            bodyMinMax[1] = data["td1"][t]

tsetData = [data["tset"][t] if data["tset"][t] > 0 and data["tset"][t] < 100 and data["stage"][t] == stage else float('nan')
    for t in range(len(xs))]

ax[3].plot( xs, tsetData, color="g", label = 'Т.отбора' )

if data["info"]["hysteresis"] > 0:
    hystData = [t + data["info"]["hysteresis"] if not math.isnan(t) else float('nan') for t in tsetData]
    ax[3].plot( xs, hystData, color="r", label = "Гистерезис")
if data["info"]["predecrement"] > 0:
    predData = [t + data["info"]["predecrement"] if not math.isnan(t) else float('nan') for t in tsetData]
    ax[3].plot( xs, predData, color="orange", label = "Предекремент")

tempData = [t if t >= bodyMinMax[0] and t <= bodyMinMax[1] else float('nan') for t in data["td1"]]

config["addLegends"] = True
config["plotColor"] = 'b'
config["plotlabel"] = 'ТД1'
draw_plot( ax[3], config, tempData, "Температура", "{:.2f}C" )

ax[3].legend( loc='upper left' )

# TD2 GRAPH
config["plotlabel"] = 'ТД2'
draw_plot( ax[4], config, data["td2"], "ТД2, C", "{:.2f}C" )
ax[4].axhline(92.0, color="r", label = '92C', linestyle="--")
ax[4].axhline(94.0, color="orange", label = '94C', linestyle="--")
ax[4].legend( loc='upper left' )

# PRESSURE GRAPH
config["addLegends"] = False
config["plotColor"] = '0.5' # gray
config["labels"] = labels # last plot, show tick labels
ax[5].tick_params("x", rotation=45)
draw_plot( ax[5], config, data["pressure"], "Атм.давл, мм рт ст", "{:.1f}" )

# we're done.
plt.savefig( outfile, dpi=300, bbox_inches='tight' )
#plt.show()
