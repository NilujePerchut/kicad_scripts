#!/usr/bin/env python

# Teardrop for pcbnew using filled zones
# (c) Niluje 2016 thewireddoesntexist.org
#
# Based on Teardrops for PCBNEW by svofski, 2014 http://sensi.org/~svo

import os, sys
import argparse
import fileinput
from math import cos, acos, sin, asin, tan, atan2, degrees
from pcbnew import *

__version__ = "0.3.1"

ToUnits=ToMM
FromUnits=FromMM

def __File2List(filename):
    try:
        f = open(filename, 'r')
        listfile = [ l.rstrip() for l in f ]
    except IOError:
        return []
    f.close()
    return listfile

def __List2File(thelist, filename):
    f = open(filename, 'w')
    for l in thelist:
        f.write(l+'\n')
    f.close()

def __GetAllVias(board):
    """Just retreive all via from the given board"""
    vias = []
    vias_selected =[]
    for item in board.GetTracks():
        if type(item) == VIA:
            pos = item.GetPosition()
            width = item.GetWidth()
            drill = item.GetDrillValue()
            vias.append((pos, width, drill))
            if item.IsSelected():
                vias_selected.append((pos, width, drill))
    return vias, vias_selected

def __GetAllPads(board, filters=[]):
    """Just retreive all pads from the given board"""
    pads = []
    pads_selected = []
    for i in xrange(board.GetPadCount()):
        pad = board.GetPad(i)
        if pad.GetAttribute() in filters:
            pos = pad.GetPosition()
            drill = min(pad.GetSize())
            pads.append((pos, drill ))
            if pad.IsSelected():
                pads_selected.append((pos, drill))
    return pads, pads_selected

def __Zone(viafile, board, points, track):
    """Add a zone to the board"""
    z = ZONE_CONTAINER(board)

    #Add zone properties
    z.SetLayer(track.GetLayer())
    z.SetNetCode(track.GetNetCode())
    z.SetZoneClearance(track.GetClearance())
    z.SetMinThickness(25400) #The minimum
    z.SetPadConnection(2) # 2 -> solid
    z.SetIsFilled(True)

    line=[]
    for p in points:
        z.Outline().AppendCorner(p.x, p.y)
        line.append(str(p))
    z.Outline().CloseLastContour()

    line.sort()
    z.BuildFilledSolidAreasPolygons(board)

    #Save zone properties
    vialine = track.GetLayerName() + ':' + ''.join(line)
    if not vialine in viafile:
        viafile.append(vialine)
        return z

    return None

def __Bezier(p1, p2, p3, n=20.0):
    n = float(n)
    pts = []
    for i in range(int(n)+1):
        t = i/n
        a = (1.0 - t) ** 2
        b = 2.0*t*(1.0-t)
        c = t**2

        x = int(a * p1[0] + b * p2[0] + c * p3[0])
        y = int(a * p1[1] + b * p2[1] + c * p3[1])
        pts.append(wxPoint(x,y))
    return pts

def __ComputeCurved(vpercent, w, vec, via, pts, segs):
    """Compute the curves part points"""

    radius = via[1]/2.0

    #Compute the bezier middle points
    req_angle = asin(vpercent/100.0);
    oppside = tan(req_angle)*(radius-(w/sin(req_angle)))
    length = sqrt(radius*radius + oppside*oppside)
    d = req_angle - acos(radius/length)
    vecBC = [vec[0]*cos(d)+vec[1]*sin(d) , -vec[0]*sin(d)+vec[1]*cos(d)]
    pointBC = via[0] + wxPoint(int(vecBC[0] * length), int(vecBC[1] * length))
    d = -d
    vecAE = [vec[0]*cos(d)+vec[1]*sin(d) , -vec[0]*sin(d)+vec[1]*cos(d)]
    pointAE = via[0] + wxPoint(int(vecAE[0] * length), int(vecAE[1] * length))

    curve1 = __Bezier(pts[1], pointBC, pts[2], n=segs)
    curve2 = __Bezier(pts[4], pointAE, pts[0], n=segs)

    return curve1 + [pts[3]] + curve2

def __ComputePoints(track, via, hpercent, vpercent, segs):
    """Compute all teardrop points"""
    start = track.GetStart()
    end = track.GetEnd()

    if (segs>2) and (vpercent>70.0):
        #If curved via are selected, max angle is 45 degres --> 70%
        vpercent = 70.0

    # ensure that start is at the via/pad end
    d = end - via[0]
    if sqrt(d.x * d.x + d.y * d.y) < via[1]:
        start, end = end, start

    # get normalized track vector
    # it will be used a base vector pointing in the track direction
    pt = end - start
    norm = sqrt(pt.x * pt.x + pt.y * pt.y)
    vec = [t / norm for t in pt]

    # find point on the track, sharp end of the teardrop
    w = track.GetWidth()/2
    radius = via[1]/2
    n = radius*(1+hpercent/100.0)
    dist = sqrt(n*n + w*w)
    d = atan2(w, n)
    vecB = [vec[0]*cos(d)+vec[1]*sin(d) , -vec[0]*sin(d)+vec[1]*cos(d)]
    pointB = start + wxPoint(int(vecB[0] * dist), int(vecB[1] * dist))
    vecA = [vec[0]*cos(-d)+vec[1]*sin(-d) , -vec[0]*sin(-d)+vec[1]*cos(-d)]
    pointA = start + wxPoint(int(vecA[0] * dist), int(vecA[1] * dist))

    # via side points
    radius = via[1] / 2
    d = asin(vpercent/100.0);
    vecC = [vec[0]*cos(d)+vec[1]*sin(d) , -vec[0]*sin(d)+vec[1]*cos(d)]
    d = asin(-vpercent/100.0);
    vecE = [vec[0]*cos(d)+vec[1]*sin(d) , -vec[0]*sin(d)+vec[1]*cos(d)]
    pointC = via[0] + wxPoint(int(vecC[0] * radius), int(vecC[1] * radius))
    pointE = via[0] + wxPoint(int(vecE[0] * radius), int(vecE[1] * radius))

    # Introduce a last point in order to cover the via centre.
    # If not, the zone won't be filled
    vecD = [-vec[0], -vec[1]]
    radius = (via[1]/2)*0.5 #50% of via radius is enough to include
    pointD = via[0] + wxPoint(int(vecD[0] * radius), int(vecD[1] * radius))

    pts = [pointA, pointB, pointC, pointD, pointE]
    if segs > 2:
        pts = __ComputeCurved(vpercent, w, vec, via, pts, segs)

    return pts

def SetTeardrops(hpercent=30, vpercent=70, segs=10):
    """Set teardrops on a teardrop free board"""

    pcb = GetBoard()
    td_filename = pcb.GetFileName() + '_td'

    vias = __GetAllVias(pcb)[0] + __GetAllPads(pcb, [PAD_ATTRIB_STANDARD])[0]
    vias_selected = __GetAllVias(pcb)[1] +\
                    __GetAllPads(pcb, [PAD_ATTRIB_STANDARD])[1]
    viasfile = __File2List(td_filename)
    if len(vias_selected) > 0:
        print('Using selected pads/vias')
        vias = vias_selected
    else:
        # If a teardrop file is present AND no pad are selected,
        # remove all teardrops.
        if len(viasfile) > 0:
            RmTeardrops()

    count = 0
    for track in pcb.GetTracks():
        if type(track) == TRACK:
            for via in vias:
                if track.IsPointOnEnds(via[0], via[1]/2):
                    if (track.GetLength() < via[1]) or\
                        (track.GetWidth() >= via[1] * vpercent / 100.0):
                        continue
                    coor = __ComputePoints(track, via, hpercent, vpercent,
                                           segs)
                    the_zone = __Zone(viasfile, pcb, coor, track)
                    if the_zone:
                        pcb.Add(the_zone)
                        count = count + 1

    if len(viasfile) > 0:
        __List2File(viasfile, td_filename)
    else:
        #Just remove the file
        try:
            os.remove(td_filename)
        except IOError:
            #There was no file at startup and no teardrop to add
            pass
        except OSError:
            #There was no file at startup and no teardrop to add
            pass

    print('{0} teardrops inserted'.format(count))

def __RemoveTeardropsInList(pcb, tdlist):
    """Remove all teardrops mentioned in the list if available in current PCB.
       Returns number of deleted pads"""
    to_remove=[]
    for line in tdlist:
        for z in [ pcb.GetArea(i) for i in range(pcb.GetAreaCount()) ]:
            corners = [str(z.GetCornerPosition(i))
                       for i in range(z.GetNumCorners())]
            corners.sort()
            if line.rstrip() == z.GetLayerName() + ':' + ''.join(corners):
                to_remove.append(z)

    count = len(to_remove)
    for tbr in to_remove:
        pcb.Remove(tbr)
    #Remove the td file
    try:
        os.remove(pcb.GetFileName() + '_td')
    except OSError:
        pass

    return count

def __RemoveSelectedTeardrops(pcb, tdlist, sel):
    """Remove only the selected teardrops if mentionned in teardrops file.
       Also update the teardrops file"""
    print('Not implemented yet')
    return 0

def RmTeardrops():
    """Remove teardrops according to teardrops definition file"""

    pcb = GetBoard()
    td_filename = pcb.GetFileName() + '_td'
    viasfile = __File2List(td_filename)
    vias_selected = __GetAllVias(pcb)[1] +\
                                 __GetAllPads(pcb, [PAD_ATTRIB_STANDARD])[1]

    if len(vias_selected) > 0:
        #Only delete selected teardrops. We need to recompute the via structure
        #in order to found it in the viasfile and delete it
        count = __RemoveSelectedTeardrops(pcb, viasfile, vias_selected)
    else:
        #Delete every teardrops mentionned in the teardrops file
        count = __RemoveTeardropsInList(pcb, viasfile)

    print('{0} teardrops removed'.format(count))
