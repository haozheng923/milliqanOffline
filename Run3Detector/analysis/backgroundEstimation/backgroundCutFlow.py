


import sys

sys.path.append('/root/lib/')

import ROOT as r
import os
import json
import pandas as pd
import uproot 
import awkward as ak
import array as arr
import numpy as np
import shutil
import itertools

sys.path.append(os.path.dirname(__file__) + '/../utilities/')
from milliqanProcessor import *
from milliqanScheduler import *
from milliqanCuts import *
from milliqanPlotter import *
from utilities import *


if __name__ == "__main__":

    beam = False
    skim = True
    outputFile = 'bgCutFlow_output.root'
    qualityLevel = 'Tight'
    maxEvents = None
    stepSize = 1000

    filelist = [     
        #"/home/mcarrigan/scratch0/milliQan/analysis/milliqanOffline/Run3Detector/analysis/skim/MilliQan_Run1800_v35_signalSkim_beamOff_tight.root",
        #"/home/mcarrigan/scratch0/milliQan/analysis/milliqanOffline/Run3Detector/analysis/skim/MilliQan_Run1700_v35_signalSkim_beamOff_tight.root",
        #"/home/mcarrigan/scratch0/milliQan/analysis/milliqanOffline/Run3Detector/analysis/skim/MilliQan_Run1600_v35_signalSkim_beamOff_tight.root",
        #"/home/mcarrigan/scratch0/milliQan/analysis/milliqanOffline/Run3Detector/analysis/skim/MilliQan_Run1500_v35_signalSkim_beamOff_tight.root",
        "/home/mcarrigan/scratch0/milliQan/analysis/milliqanOffline/Run3Detector/analysis/skim/MilliQan_Run1500_v35_signalSkim3Line_beamOff_tight.root",
        ]

    if skim:
        qualityLevel = 'override'

    print("Running on files {}".format(filelist))

    goodRunsName = '/eos/experiment/milliqan/Configs/goodRunsList.json'
    lumisName = '/eos/experiment/milliqan/Configs/mqLumis.json'
    shutil.copy(goodRunsName, 'goodRunsList.json')
    shutil.copy(lumisName, 'mqLumis.json')

    goodRuns = loadJson('goodRunsList.json')
    lumis = loadJson('mqLumis.json')

    if skim:
        lumi, runTime = getSkimLumis(filelist)
    else:
        lumi, runTime = getLumiofFileList(filelist)

    #define the necessary branches to run over
    branches = ['event', 'tTrigger', 'boardsMatched', 'pickupFlag', 'fileNumber', 'runNumber', 'type', 'ipulse', 'nPE', 'chan',
                'time_module_calibrated', 'timeFit_module_calibrated', 'row', 'column', 'layer', 'height', 'area', 'npulses', 'sidebandRMS']


    #define the milliqan cuts object
    mycuts = milliqanCuts()

    #require pulses are in trigger window
    centralTimeCut = getCutMod(mycuts.centralTime, mycuts, 'centralTimeCut', cut=True)

    #require pulses are not pickup
    pickupCut = getCutMod(mycuts.pickupCut, mycuts, 'pickupCut', cut=True)

    #require that all digitizer boards are matched
    boardMatchCut = getCutMod(mycuts.boardsMatched, mycuts, 'boardMatchCut', cut=True, branches=branches)

    #greater than or equal to one hit per layer
    hitInAllLayers = getCutMod(mycuts.oneHitPerLayerCut, mycuts, 'hitInAllLayers', cut=True, multipleHits=True)

    #exactly one hit per layer
    oneHitPerLayer = getCutMod(mycuts.oneHitPerLayerCut, mycuts, 'oneHitPerLayer', cut=True, multipleHits=False)

    #panel veto
    panelVeto = getCutMod(mycuts.panelVeto, mycuts, 'panelVeto', cut=True, nPECut=1e4)

    #first pulse max
    firstPulseMax = getCutMod(mycuts.firstPulseMax, mycuts, 'firstPulseMax', cut=True)

    #veto events with an early pulse
    vetoEarlyPulse = getCutMod(mycuts.vetoEarlyPulse, mycuts, 'vetoEarlyPulse', cut=True)

    #four in line cut
    straightLineCut = getCutMod(mycuts.straightLineCut, mycuts, 'straightLineCut', cut=True)

    #npe max-min < 10 cut
    nPEMaxMin = getCutMod(mycuts.nPEMaxMin, mycuts, 'nPEMaxMin', nPECut=20, cut=True)

    #time max-min < 15 cut
    timeMaxMin = getCutMod(mycuts.timeMaxMin, mycuts, 'timeMaxMin', timeCut=40, cut=True)

    #veto events with large hit in front/back panels
    beamMuonPanelVeto = getCutMod(mycuts.beamMuonPanelVeto, mycuts, 'beamMuonPanelVeto', cut=True, nPECut=5e4)

    #require # bars in event  < cut
    nBarsCut = getCutMod(mycuts.nBarsCut, mycuts, 'nBarsCut', nBarsCut=15, cut=True)

    #require < nBars within deltaT
    nBarsDeltaTCut = getCutMod(mycuts.nBarsDeltaTCut, mycuts, 'nBarsDeltaTCut', nBarsCut=10, timeCut=100, cut=True)

    #sideband RMS cut
    sidebandRMSCut = getCutMod(mycuts.sidebandRMSCut, mycuts, 'sidebandRMSCut', cutVal=2, cut=True)

    #use first pulse in a channel only
    firstPulseCut = getCutMod(mycuts.firstPulseCut, mycuts, 'firstPulseCut', cut=True)

    #cut out all pulses except bars
    barsCut = getCutMod(mycuts.barCut, mycuts, 'barCut', cut=True)

    #define histograms
    h_timeDiff1 = r.TH1F('h_timeDiff1', "Layer 3 and 0 Time Difference", 100, -50, 50)
    h_timeDiff2 = r.TH1F('h_timeDiff2', "Layer 3 and 0 Time Difference", 100, -50, 50)
    h_timeDiff3 = r.TH1F('h_timeDiff3', "Layer 3 and 0 Time Difference", 100, -50, 50)
    h_timeDiff4 = r.TH1F('h_timeDiff4', "Layer 3 and 0 Time Difference", 100, -50, 50)
    h_timeDiff5 = r.TH1F('h_timeDiff5', "Layer 3 and 0 Time Difference", 100, -50, 50)
    h_timeDiff6 = r.TH1F('h_timeDiff6', "Layer 3 and 0 Time Difference", 100, -50, 50)
    h_timeDiff7 = r.TH1F('h_timeDiff7', "Layer 3 and 0 Time Difference", 100, -50, 50)
    h_timeDiff8 = r.TH1F('h_timeDiff8', "Layer 3 and 0 Time Difference", 100, -50, 50)
    h_timeDiff9 = r.TH1F('h_timeDiff9', "Layer 3 and 0 Time Difference", 100, -50, 50)

    h_nBars = r.TH1F('h_nBars', "Number of Bars per Event;# Bars;# Events", 64, 0, 64)
    h_nLayersBeforeAllLayers = r.TH1F('h_nLayersBeforeAllLayers', 'Number of Layers Hit Before N Layers Cut;Layers;Events', 5, 0, 5)
    h_nLayersAfterAllLayers = r.TH1F('h_nLayersAfterAllLayers', 'Number of Layers Hit After N Layers Cut;Layers;Events', 5, 0, 5)
    h_nHitsPerLayerBefore = r.TH1F('h_nHitsPerLayerBefore', 'Number of Hits Per Layer Before All Layers Hit Cut;nHits per Layer;Events*Layers', 16, 0, 16)
    h_nHitsPerLayerAfter = r.TH1F('h_nHitsPerLayerAfter', 'Number of Hits Per Layer After All Layers Hit Cut;nHits per Layer;Events*Layers', 16, 0, 16)
    h_nLayersBeforeOneHitPerLayer = r.TH1F('h_nLayersBeforeOneHitPerLayer', 'Number of Layers Hit Before One Hit Per Layer;Layers;Events', 5, 0, 5)
    h_nLayersAfterOneHitPerLayer = r.TH1F('h_nLayersAfterOneHitPerLayer', 'Number of Layers Hit After One Hit Per Layer;Layers;Events', 5, 0, 5)
    h_nBarsBeforeCut = r.TH1F('h_nBarsBeforeCut', 'Number of Bars Before Bar Cut;Bars;Events', 64, 0, 64)
    h_nBarsAfterCut = r.TH1F('h_nBarsAfterCut', 'Number of Bars After Bar Cut;Bars;Events', 64, 0, 64)
    h_nBarsInWindowBefore = r.TH1F('h_nBarsInWindowBefore', 'Number of Bars within Timing Window Before Cut;Bars;Events', 20, 0, 20)
    h_nBarsInWindowAfter = r.TH1F("h_nBarsInWindowAfter", 'Number of Bars Within Timing Window After Cut;Bars;Events', 20, 0, 20)
    h_sidebandsBefore = r.TH1F('h_sidebandsBefore', 'Sideband RMS Before Cut;Sideband RMS;Events', 50, 0, 10)
    h_sidebandsAfter = r.TH1F('h_sidebandsAfter', 'Sideband RMS After Cut;Sideband RMS;Events', 50, 0, 10)
    h_panelNPEBefore = r.TH1F('h_panelNPEBefore', 'nPE in Panels Before Cut;nPE;Panel Hits', 100, 0, 1e5)
    h_panelNPEAfter = r.TH1F('h_panelNPEAfter', 'nPE in Panels After Cut;nPE;Panel Hits', 100, 0, 1e5)
    h_panelHitsBefore = r.TH1F('h_panelHitsBefore', 'Number of Panel Hits Before Cut;# Panels;Events', 10, 0, 10)
    h_panelHitsAfter = r.TH1F('h_panelHitsAfter', 'Number of Panel Hits After Cut;# Panels;Events', 10, 0, 10)
    h_frontPanelNPEBefore = r.TH1F('h_frontPanelNPEBefore', 'nPE of Front Panel Before Cut;nPE;# Pulses', 300, 0, 3e5)
    h_frontPanelNPEAfter = r.TH1F('h_frontPanelNPEAfter', 'nPE of Front Panel After Cut;nPE;# Pulses', 300, 0, 3e5)
    h_backPanelNPEBefore = r.TH1F('h_backPanelNPEBefore', 'nPE of Back Panel Before Cut;nPE;# Pulses', 300, 0, 3e5)
    h_backPanelNPEAfter = r.TH1F('h_backPanelNPEAfter', 'nPE of Back Panel After Cut;nPE;# Pulses', 300, 0, 3e5)
    h_straightTimeBefore = r.TH1F('h_straightTimeBefore', 'Pulse Times Before Straight Line Cut;Time;# Pulses', 240, 0, 2400)
    h_straightTimeAfter = r.TH1F('h_straightTimeAfter', 'Pulse Times After Straight Line Cut;Time;# Pulses', 240, 0, 2400)
    h_straightNPEBefore = r.TH1F('h_straightNPEBefore', 'nPE of Pulses Before Straight Line Cut;nPE;# Pulses', 100, 0, 100)
    h_straightNPEAfter = r.TH1F('h_straightNPEAfter', 'nPE of Pulses After Straight Line Cut;nPE; # Pulses', 100, 0, 100)
    h_straightHeightBefore = r.TH1F('h_straightHeightBefore', 'Height of Pulses Before Straight Line Cut;Height;# Pulses', 1400, 0, 1400)
    h_straightHeightAfter = r.TH1F('h_straightHeightAfter', 'Height of Pulses After Straight Line Cut;Height;# Pulses', 1400, 0, 1400)
    h_straightChannelBefore = r.TH1F('h_straightChannelBefore', 'Channels Before Straight Line Cut;Channel;# Pulses', 80, 0, 80)
    h_straightChannelAfter = r.TH1F('h_straightChannelAfter', 'Channels After Straight Line Cut;Channel; # Pulses', 80, 0, 80)
    h_straightNumPaths = r.TH1F('h_straightNumPaths', "Number of Straight Line Paths in Event;Num Paths;Events", 16, 0, 16)
    h_maxNPEBefore = r.TH1F('h_maxNPEBefore', 'Max NPE in Event Before Cut;Max NPE;Events', 100, 0, 100)
    h_minNPEBefore = r.TH1F('h_minNPEBefore', 'Min NPE in Event Before Cut;Min NPE;Events', 100, 0, 100)
    h_maxNPEAfter = r.TH1F('h_maxNPEAfter', 'Max NPE in Event After Cut;Max NPE;Events', 100, 0, 100)
    h_minNPEAfter = r.TH1F('h_minNPEAfter', 'Min NPE in Event After Cut;Min NPE;Events', 100, 0, 100)
    h_minTimeBefore = r.TH1F('h_minTimeBefore', 'Min Pulse Time Before Cut;Min Time;Events', 1200, 0, 2400)
    h_maxTimeBefore = r.TH1F('h_maxTimeBefore', 'Max Pulse Time Before Cut;Min Time;Events', 1200, 0, 2400)
    h_minTimeAfter = r.TH1F('h_minTimeAfter', 'Min Pulse Time After Cut;Min Time;Events', 1200, 0, 2400)
    h_maxTimeAfter = r.TH1F('h_maxTimeAfter', 'Max Pulse Time After Cut;Min Time;Events', 1200, 0, 2400)

    #define milliqan plotter
    myplotter = milliqanPlotter()
    myplotter.dict.clear()

    myplotter.addHistograms(h_timeDiff1, 'timeDiff')
    myplotter.addHistograms(h_timeDiff2, 'timeDiff')
    myplotter.addHistograms(h_timeDiff3, 'timeDiff')
    myplotter.addHistograms(h_timeDiff4, 'timeDiff')
    myplotter.addHistograms(h_timeDiff5, 'timeDiff')
    myplotter.addHistograms(h_timeDiff6, 'timeDiff')
    myplotter.addHistograms(h_timeDiff7, 'timeDiff')
    myplotter.addHistograms(h_timeDiff8, 'timeDiff')
    myplotter.addHistograms(h_timeDiff9, 'timeDiff')
    myplotter.addHistograms(h_nBars, 'countNBars', 'first')
    myplotter.addHistograms(h_nLayersBeforeAllLayers, 'nLayers', 'first')
    myplotter.addHistograms(h_nLayersAfterAllLayers, 'nLayers', 'first')
    myplotter.addHistograms(h_nHitsPerLayerBefore, 'nHitsPerLayerBefore')
    myplotter.addHistograms(h_nHitsPerLayerAfter, 'nHitsPerLayerAfter')
    myplotter.addHistograms(h_nLayersBeforeOneHitPerLayer, 'nLayers', 'first')
    myplotter.addHistograms(h_nLayersAfterOneHitPerLayer, 'nLayers', 'first')
    myplotter.addHistograms(h_nBarsBeforeCut, 'countNBars', 'first')
    myplotter.addHistograms(h_nBarsAfterCut, 'countNBars', 'first')
    myplotter.addHistograms(h_nBarsInWindowBefore, 'nBarsInWindowBefore', 'first')
    myplotter.addHistograms(h_nBarsInWindowAfter, 'nBarsInWindow', 'first')
    myplotter.addHistograms(h_sidebandsBefore, 'sidebandsBeforeCut')
    myplotter.addHistograms(h_sidebandsAfter, 'sidebandsAfterCut')
    myplotter.addHistograms(h_panelNPEBefore, 'panelVetoNPEBefore')
    myplotter.addHistograms(h_panelNPEAfter, 'panelVetoNPEAfter')
    myplotter.addHistograms(h_panelHitsBefore, 'panelVetoHitsBefore', 'first')
    myplotter.addHistograms(h_panelHitsAfter, 'panelVetoHitsAfter', 'first')
    myplotter.addHistograms(h_frontPanelNPEBefore, 'frontPanelNPEBefore')
    myplotter.addHistograms(h_frontPanelNPEAfter, 'frontPanelNPEAfter')
    myplotter.addHistograms(h_backPanelNPEBefore, 'backPanelNPEBefore')
    myplotter.addHistograms(h_backPanelNPEAfter, 'backPanelNPEAfter')
    myplotter.addHistograms(h_straightChannelBefore, 'chan')
    myplotter.addHistograms(h_straightChannelAfter, 'chan')
    myplotter.addHistograms(h_straightHeightBefore, 'height')
    myplotter.addHistograms(h_straightHeightAfter, 'height')
    myplotter.addHistograms(h_straightNPEBefore, 'nPE')
    myplotter.addHistograms(h_straightNPEAfter, 'nPE')
    myplotter.addHistograms(h_straightTimeBefore, 'timeFit_module_calibrated')
    myplotter.addHistograms(h_straightTimeAfter, 'timeFit_module_calibrated')
    myplotter.addHistograms(h_straightNumPaths, 'numStraightPaths')
    myplotter.addHistograms(h_maxNPEBefore, 'maxNPEBefore')
    myplotter.addHistograms(h_minNPEBefore, 'minNPEBefore')
    myplotter.addHistograms(h_maxNPEAfter, 'maxNPEAfter')
    myplotter.addHistograms(h_minNPEAfter, 'minNPEAfter')
    myplotter.addHistograms(h_minTimeBefore, 'minTimeBefore')
    myplotter.addHistograms(h_maxTimeBefore, 'maxTimeBefore')
    myplotter.addHistograms(h_minTimeAfter, 'minTimeAfter')
    myplotter.addHistograms(h_maxTimeAfter, 'maxTimeAfter')

    cutflow = [mycuts.totalEventCounter, mycuts.fullEventCounter, 
                mycuts.timeDiff,
                boardMatchCut, 
                pickupCut, 
                firstPulseCut,
                centralTimeCut,
                mycuts.nLayersCut,
                mycuts.countNBars, 

                myplotter.dict['h_nLayersBeforeAllLayers'],
                hitInAllLayers,
                myplotter.dict['h_nLayersAfterAllLayers'],
                myplotter.dict['h_nHitsPerLayerBefore'],
                myplotter.dict['h_nHitsPerLayerAfter'],

                myplotter.dict['h_nBarsBeforeCut'],
                nBarsCut,
                myplotter.dict['h_nBarsAfterCut'],

                panelVeto,                

                beamMuonPanelVeto,

                barsCut,

                nBarsDeltaTCut,

                sidebandRMSCut,

                myplotter.dict['h_nBars'],

                #myplotter.dict['h_nLayersBeforeOneHitPerLayer'],
                #oneHitPerLayer,
                #myplotter.dict['h_nLayersAfterOneHitPerLayer'],

                firstPulseMax,

                vetoEarlyPulse,
                
                nPEMaxMin,
                myplotter.dict['h_maxNPEBefore'],
                myplotter.dict['h_minNPEBefore'],
                myplotter.dict['h_maxNPEAfter'],
                myplotter.dict['h_minNPEAfter'],

                myplotter.dict['h_straightTimeBefore'],
                myplotter.dict['h_straightNPEBefore'],
                myplotter.dict['h_straightHeightBefore'],
                myplotter.dict['h_straightChannelBefore'],
                straightLineCut,
                myplotter.dict['h_straightTimeAfter'],
                myplotter.dict['h_straightNPEAfter'],
                myplotter.dict['h_straightHeightAfter'],
                myplotter.dict['h_straightChannelAfter'],
                myplotter.dict['h_straightNumPaths'],
                
                timeMaxMin,
                myplotter.dict['h_minTimeBefore'],
                myplotter.dict['h_maxTimeBefore'],
                myplotter.dict['h_minTimeAfter'],
                myplotter.dict['h_maxTimeAfter'],

            ]

    for key, value in myplotter.dict.items():
        if value not in cutflow:
            cutflow.append(value)

    #create a schedule of the cuts
    myschedule = milliQanScheduler(cutflow, mycuts, myplotter)

    #print out the schedule
    myschedule.printSchedule()

    #create the milliqan processor object
    myiterator = milliqanProcessor(filelist, branches, myschedule, step_size=stepSize, qualityLevel=qualityLevel, max_events=maxEvents, goodRunsList=os.getcwd()+'/goodRunsList.json')

    #run the milliqan processor
    myiterator.run()

    myschedule.cutFlowPlots()

    #save plots
    myplotter.saveHistograms(outputFile)
    print("--------------------------------------------------------")
    print("|\033[1;34m Total run time {}s and luminosity {}pb^-1 \033[0m|".format(runTime, lumi))
    print("--------------------------------------------------------")

    mycuts.getCutflowCounts()