#!/usr/bin/env python

# Teardrop for pcbnew using filled zones
# (c) Niluje 2019 thewireddoesntexist.org
#
# Based on Teardrops for PCBNEW by svofski, 2014 http://sensi.org/~svo

import os
import sys
from math import cos, acos, sin, asin, tan, atan2, sqrt
from pcbnew import VIA, ToMM, TRACK, FromMM, wxPoint, GetBoard, ZONE_CONTAINER
from pcbnew import PAD_ATTRIB_STANDARD, PAD_ATTRIB_SMD, ZONE_FILLER

__version__ = "0.4.6"

ToUnits = ToMM
FromUnits = FromMM

MAGIC_TEARDROP_ZONE_ID = 0x4242


def __GetAllVias(board):
    """Just retreive all via from the given board"""
    vias = []
    vias_selected = []
    for item in board.GetTracks():
        if type(item) == VIA:
            pos = item.GetPosition()
            width = item.GetWidth()
            drill = item.GetDrillValue()
            layer = "all"
            vias.append((pos, width, drill, layer))
            if item.IsSelected():
                vias_selected.append((pos, width, drill, layer))
    return vias, vias_selected


def __GetAllPads(board, filters=[]):
    """Just retreive all pads from the given board"""
    pads = []
    pads_selected = []
    for i in range(board.GetPadCount()):
        pad = board.GetPad(i)
        if pad.GetAttribute() in filters:
            pos = pad.GetPosition()
            drill = min(pad.GetSize())
            """See where the pad is"""
            if pad.GetAttribute() == PAD_ATTRIB_SMD:
                if pad.IsOnLayer(0):
                    layer = "front"
                else:
                    layer = "back"
            else:
                layer = "all"
            pads.append((pos, drill, 0, layer))
            if pad.IsSelected():
                pads_selected.append((pos, drill, 0, layer))
    return pads, pads_selected


def __GetAllTeardrops(board):
    """Just retrieves all teardrops of the current board classified by net"""
    teardrops_zones = {}
    for zone in [board.GetArea(i) for i in range(board.GetAreaCount())]:
        if zone.GetPriority() == MAGIC_TEARDROP_ZONE_ID:
            netname = zone.GetNetname()
            if netname not in teardrops_zones.keys():
                teardrops_zones[netname] = []
            teardrops_zones[netname].append(zone)
    return teardrops_zones


def __DoesTeardropBelongTo(teardrop, track, via):
    """Return True if the teardrop covers given track AND via"""
    # First test if the via belongs to the teardrop
    if not teardrop.HitTestInsideZone(via[0]):
        return False
    # In a second time, test if the track belongs to the teardrop
    if not track.HitTest(teardrop.GetBoundingBox().GetCenter()):
        return False
    return True


def __Zone(board, points, track):
    """Add a zone to the board"""
    z = ZONE_CONTAINER(board)

    # Add zone properties
    z.SetLayer(track.GetLayer())
    z.SetNetCode(track.GetNetCode())
    z.SetZoneClearance(track.GetClearance())
    z.SetMinThickness(25400)  # The minimum
    z.SetPadConnection(2)  # 2 -> solid
    z.SetIsFilled(True)
    z.SetPriority(MAGIC_TEARDROP_ZONE_ID)
    ol = z.Outline()
    ol.NewOutline()

    for p in points:
        ol.Append(p.x, p.y)

    sys.stdout.write("+")
    return z


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
        pts.append(wxPoint(x, y))
    return pts


def __TeardropLength(track, via, hpercent):
    """Computes the teardrop length"""
    n = min(track.GetLength(), (via[1] - track.GetWidth()) * 1.2071)
    n = max(via[1]*(0.5+hpercent/200.0), n)
    return n


def __ComputeCurved(vpercent, w, vec, via, pts, segs):
    """Compute the curves part points"""

    radius = via[1]/2.0

    # Compute the bezier middle points
    req_angle = asin(vpercent/100.0)
    oppside = tan(req_angle)*(radius-(w/sin(req_angle)))
    length = sqrt(radius*radius + oppside*oppside)
    d = req_angle - acos(radius/length)
    vecBC = [vec[0]*cos(d)+vec[1]*sin(d), -vec[0]*sin(d)+vec[1]*cos(d)]
    pointBC = via[0] + wxPoint(int(vecBC[0] * length), int(vecBC[1] * length))
    d = -d
    vecAE = [vec[0]*cos(d)+vec[1]*sin(d), -vec[0]*sin(d)+vec[1]*cos(d)]
    pointAE = via[0] + wxPoint(int(vecAE[0] * length), int(vecAE[1] * length))

    curve1 = __Bezier(pts[1], pointBC, pts[2], n=segs)
    curve2 = __Bezier(pts[4], pointAE, pts[0], n=segs)

    return curve1 + [pts[3]] + curve2


def __ComputePoints(track, via, hpercent, vpercent, segs):
    """Compute all teardrop points"""
    start = track.GetStart()
    end = track.GetEnd()

    if (segs > 2) and (vpercent > 70.0):
        # If curved via are selected, max angle is 45 degres --> 70%
        vpercent = 70.0

    # ensure that start is at the via/pad end
    d = end - via[0]
    if sqrt(d.x * d.x + d.y * d.y) < via[1]/2.0:
        start, end = end, start

    # get normalized track vector
    # it will be used a base vector pointing in the track direction
    pt = end - start
    norm = sqrt(pt.x * pt.x + pt.y * pt.y)
    vec = [t / norm for t in pt]

    # find point on the track, sharp end of the teardrop
    w = track.GetWidth()/2
    radius = via[1]/2
    n = __TeardropLength(track, via, hpercent)
    dist = sqrt(n*n + w*w)
    d = atan2(w, n)
    vecB = [vec[0]*cos(d)+vec[1]*sin(d), -vec[0]*sin(d)+vec[1]*cos(d)]
    pointB = start + wxPoint(int(vecB[0] * dist), int(vecB[1] * dist))
    vecA = [vec[0]*cos(-d)+vec[1]*sin(-d), -vec[0]*sin(-d)+vec[1]*cos(-d)]
    pointA = start + wxPoint(int(vecA[0] * dist), int(vecA[1] * dist))

    # via side points
    radius = via[1] / 2
    d = asin(vpercent/100.0)
    vecC = [vec[0]*cos(d)+vec[1]*sin(d), -vec[0]*sin(d)+vec[1]*cos(d)]
    d = asin(-vpercent/100.0)
    vecE = [vec[0]*cos(d)+vec[1]*sin(d), -vec[0]*sin(d)+vec[1]*cos(d)]
    pointC = via[0] + wxPoint(int(vecC[0] * radius), int(vecC[1] * radius))
    pointE = via[0] + wxPoint(int(vecE[0] * radius), int(vecE[1] * radius))

    # Introduce a last point in order to cover the via centre.
    # If not, the zone won't be filled
    vecD = [-vec[0], -vec[1]]
    radius = (via[1]/2)*0.5  # 50% of via radius is enough to include
    pointD = via[0] + wxPoint(int(vecD[0] * radius), int(vecD[1] * radius))

    pts = [pointA, pointB, pointC, pointD, pointE]
    if segs > 2:
        pts = __ComputeCurved(vpercent, w, vec, via, pts, segs)

    return pts


def RebuildAllZones(pcb):
    """Rebuilt all zones"""
    filler = ZONE_FILLER(pcb)
    filler.Fill(pcb.Zones())


def SetTeardrops(hpercent=30, vpercent=70, segs=10, pcb=None, use_smd=False):
    """Set teardrops on a teardrop free board"""

    if pcb is None:
        pcb = GetBoard()

    pad_types = [PAD_ATTRIB_STANDARD] + [PAD_ATTRIB_SMD]*use_smd
    vias = __GetAllVias(pcb)[0] + __GetAllPads(pcb, pad_types)[0]
    vias_selected = __GetAllVias(pcb)[1] + __GetAllPads(pcb, pad_types)[1]
    if len(vias_selected) > 0:
        vias = vias_selected

    teardrops = __GetAllTeardrops(pcb)
    count = 0
    for track in [t for t in pcb.GetTracks() if type(t)==TRACK]:
        for via in [v for v in vias if track.IsPointOnEnds(v[0], int(v[1]/2))]:
            if (track.GetLength() < __TeardropLength(track, via, hpercent)) or\
               (track.GetWidth() >= via[1] * vpercent / 100):
                continue

            found = False
            if track.GetNetname() in teardrops.keys():
                for teardrop in teardrops[track.GetNetname()]:
                    if __DoesTeardropBelongTo(teardrop, track, via):
                        found = True
                        break

            # Discard case where pad and track are not on the same layer
            if (via[3] == "front") and (not track.IsOnLayer(0)):
                continue
            if (via[3] == "back") and track.IsOnLayer(0):
                continue

            if not found:
                coor = __ComputePoints(track, via, hpercent, vpercent, segs)
                pcb.Add(__Zone(pcb, coor, track))
                count += 1

    RebuildAllZones(pcb)
    print('{0} teardrops inserted'.format(count))
    return count


def RmTeardrops(pcb=None):
    """Remove all teardrops"""

    if pcb is None:
        pcb = GetBoard()

    count = 0
    teardrops = __GetAllTeardrops(pcb)
    for netname in teardrops:
        for teardrop in teardrops[netname]:
            pcb.Remove(teardrop)
            count += 1

    RebuildAllZones(pcb)
    print('{0} teardrops removed'.format(count))
    return count
