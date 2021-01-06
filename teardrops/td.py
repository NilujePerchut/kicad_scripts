#!/usr/bin/env python

# Teardrop for pcbnew using filled zones
# (c) Niluje 2019 thewireddoesntexist.org
#
# Based on Teardrops for PCBNEW by svofski, 2014 http://sensi.org/~svo
# Cubic Bezier upgrade by mitxela, 2021 mitxela.com

import os
import sys
from math import cos, acos, sin, asin, tan, atan2, sqrt, pi
from pcbnew import VIA, ToMM, TRACK, FromMM, wxPoint, GetBoard, ZONE_CONTAINER
from pcbnew import PAD_ATTRIB_STANDARD, PAD_ATTRIB_SMD, ZONE_FILLER, VECTOR2I
from pcbnew import STARTPOINT, ENDPOINT

__version__ = "0.4.11"

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
            layer = -1
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
                # Cannot use GetLayer here because it returns the non-flipped
                # layer. Need to get the real layer from the layer set
                cu_stack = pad.GetLayerSet().CuStack()
                if len(cu_stack) == 0:
                    # The pad is not on a Copper layer
                    continue
                layer = cu_stack[0]
            else:
                layer = -1
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


def __Bezier(p1, p2, p3, p4, n=20.0):
    n = float(n)
    pts = []
    for i in range(int(n)+1):
        t = i/n
        a = (1.0 - t)**3
        b = 3.0 * t * (1.0-t)**2
        c = 3.0 * t**2 * (1.0-t)
        d = t**3

        x = int(a * p1[0] + b * p2[0] + c * p3[0] + d * p4[0])
        y = int(a * p1[1] + b * p2[1] + c * p3[1] + d * p4[1])
        pts.append(wxPoint(x, y))
    return pts


def __PointDistance(a,b):
    """Distance between two points"""
    return sqrt((a[0]-b[0])*(a[0]-b[0]) + (a[1]-b[1])*(a[1]-b[1]))

def __ComputeCurved(vpercent, w, vec, via, pts, segs):
    """Compute the curves part points"""

    # A and B are points on the track
    # C and E are points on the via
    # D is midpoint behind the via centre

    radius = via[1]/2
    minVpercent = float(w*2) / float(via[1])
    weaken = (vpercent/100.0  -minVpercent) / (1-minVpercent) / radius

    biasBC = 0.5 * __PointDistance( pts[1], pts[2] )
    biasAE = 0.5 * __PointDistance( pts[4], pts[0] )

    vecC = pts[2] - via[0]
    tangentC = [ pts[2][0] - vecC[1]*biasBC*weaken,
                 pts[2][1] + vecC[0]*biasBC*weaken ]
    vecE = pts[4] - via[0]
    tangentE = [ pts[4][0] + vecE[1]*biasAE*weaken,
                 pts[4][1] - vecE[0]*biasAE*weaken ]

    tangentB = [pts[1][0] - vec[0]*biasBC, pts[1][1] - vec[1]*biasBC]
    tangentA = [pts[0][0] - vec[0]*biasAE, pts[0][1] - vec[1]*biasAE]

    curve1 = __Bezier(pts[1], tangentB, tangentC, pts[2], n=segs)
    curve2 = __Bezier(pts[4], tangentE, tangentA, pts[0], n=segs)

    return curve1 + [pts[3]] + curve2


def __FindTouchingTrack(t1, endpoint, trackLookup):
    """Find a track connected to the end of another track"""
    match = 0
    matches = 0
    ret = False, False
    for t2 in trackLookup[t1.GetLayer()][t1.GetNetname()]:
        # The track object can change, this seems like the only
        # reliable way to test if tracks are the same
        if t2.GetStart() == t1.GetStart() and t2.GetEnd() == t1.GetEnd():
            continue
        match = t2.IsPointOnEnds(endpoint, 10)
        if match:
            # if faced with a Y junction, stop here
            matches += 1
            if matches>1:
                return False, False
            ret = match, t2
    return ret


def __NormalizeVector(pt):
    """Make vector unit length"""
    norm = sqrt(pt.x * pt.x + pt.y * pt.y)
    return [t / norm for t in pt]

def __ComputePoints(track, via, hpercent, vpercent, segs, follow_tracks,
                    trackLookup):
    """Compute all teardrop points"""
    start = track.GetStart()
    end = track.GetEnd()
    radius = via[1]/2.0
    w = track.GetWidth()/2

    if vpercent > 100:
        vpercent = 100

    # ensure that start is at the via/pad end
    if __PointDistance(end, via[0]) < radius:
        start, end = end, start

    # get normalized track vector
    # it will be used a base vector pointing in the track direction
    vecT = __NormalizeVector(end - start)

    # Find point of intersection between track and edge of via
    # This normalizes teardrop lengths
    bdelta = FromMM(0.01)
    backoff=0
    while backoff<radius:
        np = start + wxPoint( vecT[0]*backoff, vecT[1]*backoff )
        if __PointDistance(np, via[0]) >= radius:
            break
        backoff += bdelta
    start=np

    # vec now points from via to intersect point
    vec = __NormalizeVector(start - via[0])

    # choose a teardrop length
    targetLength = via[1]*(hpercent/100.0)
    n = min(targetLength, track.GetLength() - backoff)
    consumed = 0

    if follow_tracks:
        # if not long enough, attempt to walk back along the curved track
        while n+consumed < targetLength:
            match, t = __FindTouchingTrack(track, end, trackLookup)
            if (match == False):
                break
    
            # [if angle is outside tolerance: break ?]
    
            consumed += n
            n = min(targetLength-consumed, t.GetLength())
            track = t
            end = t.GetEnd()
            start = t.GetStart()
            if match != STARTPOINT:
                start, end = end, start
    
        # Track may now not point directly at via
        vecT = __NormalizeVector(end - start)

    # if shortened, shrink width too
    if n+consumed < targetLength:
        minVpercent = 100* float(w) / float(radius)
        vpercent = vpercent*n/targetLength + minVpercent*(1-n/targetLength)

    # find point on the track, sharp end of the teardrop
    pointB = start + wxPoint( vecT[0]*n +vecT[1]*w , vecT[1]*n -vecT[0]*w )
    pointA = start + wxPoint( vecT[0]*n -vecT[1]*w , vecT[1]*n +vecT[0]*w )

    # via side points
    d = asin(vpercent/100.0)
    vecC = [vec[0]*cos(d)+vec[1]*sin(d), -vec[0]*sin(d)+vec[1]*cos(d)]
    d = asin(-vpercent/100.0)
    vecE = [vec[0]*cos(d)+vec[1]*sin(d), -vec[0]*sin(d)+vec[1]*cos(d)]
    pointC = via[0] + wxPoint(int(vecC[0] * radius), int(vecC[1] * radius))
    pointE = via[0] + wxPoint(int(vecE[0] * radius), int(vecE[1] * radius))

    # Introduce a last point in order to cover the via centre.
    # If not, the zone won't be filled
    pointD = via[0] + wxPoint(int(vec[0]*-0.5*radius), int(vec[1]*-0.5*radius))

    pts = [pointA, pointB, pointC, pointD, pointE]
    if segs > 2:
        pts = __ComputeCurved(vpercent, w, vecT, via, pts, segs)

    return pts


def __IsViaAndTrackInSameNetZone(pcb, via, track):
    """Return True if the given via + track is located inside a zone of the
    same netname"""
    for zone in [pcb.GetArea(i) for i in range(pcb.GetAreaCount())]:
        # Exclude other Teardrops to speed up the process
        if zone.GetPriority() == MAGIC_TEARDROP_ZONE_ID:
            continue

        # Only consider zones on the same layer
        if not zone.IsOnLayer(track.GetLayer()):
            continue

        if (zone.GetNetname() == track.GetNetname()):
            if zone.Outline().Contains(VECTOR2I(*via[0])):
                return True
    return False


def RebuildAllZones(pcb):
    """Rebuilt all zones"""
    filler = ZONE_FILLER(pcb)
    filler.Fill(pcb.Zones())


def SetTeardrops(hpercent=50, vpercent=90, segs=10, pcb=None, use_smd=False,
                 discard_in_same_zone=True, follow_tracks=True):
    """Set teardrops on a teardrop free board"""

    if pcb is None:
        pcb = GetBoard()

    pad_types = [PAD_ATTRIB_STANDARD] + [PAD_ATTRIB_SMD]*use_smd
    vias = __GetAllVias(pcb)[0] + __GetAllPads(pcb, pad_types)[0]
    vias_selected = __GetAllVias(pcb)[1] + __GetAllPads(pcb, pad_types)[1]
    if len(vias_selected) > 0:
        vias = vias_selected

    trackLookup = {}
    if follow_tracks:
        for t in pcb.GetTracks():
            if type(t) == TRACK:
                net = t.GetNetname()
                layer = t.GetLayer()
    
                if layer not in trackLookup:
                    trackLookup[layer] = {}
                if net not in trackLookup[layer]:
                    trackLookup[layer][net]=[]
                trackLookup[layer][net].append(t)


    teardrops = __GetAllTeardrops(pcb)
    count = 0
    for track in [t for t in pcb.GetTracks() if type(t)==TRACK]:
        for via in [v for v in vias if track.IsPointOnEnds(v[0], int(v[1]/2))]:
            if (track.GetWidth() >= via[1] * vpercent / 100):
                continue

            if track.IsPointOnEnds(via[0], int(via[1]/2))==STARTPOINT|ENDPOINT:
                # both start and end are within the via
                continue

            found = False
            if track.GetNetname() in teardrops.keys():
                for teardrop in teardrops[track.GetNetname()]:
                    if __DoesTeardropBelongTo(teardrop, track, via):
                        found = True
                        break

            # Discard case where pad and track are on different layers, or the
            # pad have no copper at all (paste pads).
            if (via[3] != -1) and (via[3] != track.GetLayer()):
                continue

            # Discard case where pad/via is within a zone with the same netname
            # WARNING: this can severely reduce performance
            if discard_in_same_zone and \
               __IsViaAndTrackInSameNetZone(pcb, via, track):
                continue

            if not found:
                coor = __ComputePoints(track, via, hpercent, vpercent, segs,
                                       follow_tracks, trackLookup)
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
