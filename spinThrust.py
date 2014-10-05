

import sys,re,argparse,os
from math import *

VARIABLE_MEANING = {"a":"Thurster acceleration (g)","rot":"Rotation time (minutes)", "x":"meters right of center of rotation.","y": "meters fore of center of rotation"}

REPORT_INCREMENT=10.0
TIME_END=800.
DEFAULT_CLICK=.001

def loadVariables(fileName):
    """
    Load the variables and return the dict with their content.
    Variables are
    * a : the thrust acceleration.
    * rot : the rotation time (in minutes per cycle) of angular rotation.
    * x : the number of meters right of the center of rotation
    * y : the number of meters left of the center of rotation
    """

    """
    Everything is picked up with (whitespace allowed between words) {key}={value}
    """
    exprRE=re.compile("(\S+)\s*\=\s*(\S+)")
    vars=dict()
    for lineI in open(fileName).readlines():
        line=re.sub("#.*$","",lineI)
        for expr in exprRE.finditer(line):
            vars[expr.group(1)]=float(expr.group(2))
    for var in ["a","rot","x","y"]:
        if (vars.get(var,None)==None):
            sys.stderr.write("Need to enter %s in your file. %s=%s \n" % (var,var,VARIABLE_MEANING.get(var,"")))
            sys.exit(1)
    return vars

def d2(windowX,windowY,click,theta):
    # x component of acceleration
    vx2=(windowX[-1]-windowX[-2])/click
    vx1=(windowX[-2]-windowX[-3])/click
    ax=(vx2-vx1)/click

    # y component of acceleration
    vy2=(windowY[-1]-windowY[-2])/click
    vy1=(windowY[-2]-windowY[-3])/click
    ay=(vy2-vy1)/click

    # fore and starboard.
    fx=cos(theta)
    fy=sin(theta)

    sx=sin(theta)
    sy=-cos(theta)

    return ([ax*fx+ay*fy,ax*sx+ay*sy])

def esterr(windowX,windowY,click):
    vx2=(windowX[-1]-windowX[-2])/click
    vx1=(windowX[-2]-windowX[-3])/click
    ax=(vx2-vx1)/click

    # y component of acceleration
    vy2=(windowY[-1]-windowY[-2])/click
    vy1=(windowY[-2]-windowY[-3])/click
    ay=(vy2-vy1)/click

    vx2=(windowX[-2]-windowX[-3])/click
    vx1=(windowX[-3]-windowX[-4])/click
    errx=ax-((vx2-vx1)/click)

    # y component of acceleration
    vy2=(windowY[-2]-windowY[-3])/click
    vy1=(windowY[-3]-windowY[-4])/click
    erry=ay-(vy2-vy1)/click

    aM=sqrt(ax**2.+ay**2.)
    if (aM==0.0): aM=1.0
    return(sqrt(errx**2+erry**2)/aM)
    


    
def runSim(vars,outputFile,click=DEFAULT_CLICK):
    """
    Given the initial variables, run the simulation, and report the following data in spreadsheet format.
    * The time in seconds 
    * The current x and y components of position relative to the initial position(in kilometers).
    * The current fore and starboard components of acceleration relative to the center of rotation of the ship.
    * The approximate error in computing acceleration discretely.
    """
    x=0.0
    y=0.0
    r=sqrt(vars.get("x",0.)**2.0+vars.get("y",0.)**2.0)
    """
    get acceleration in meters per second per second.
    """
    a=9.8*vars.get("a",1.)
    """
    get angular rotation in radians per second.
    """
    omega=(1/60.)*(1./(vars.get("rot",1)))*2*pi
    sys.stderr.write("omega=%.6f\n" % omega)
    """
    initialize time and angle (relative to initial pointing.
    """
    t=0.0
    theta=0.0
    vx=0.0
    vy=0.0
    """
    run clicks for 800 seconds, reporting every 10 seconds.
    """
    windowX=[]
    windowY=[]
    lastT=0.0
    out=open(outputFile,"w")
    out.write("time\ttheta\tx\ty\ta_fore\ta_starboard\ta_magnitude\terr estimate\n")
    while(t<TIME_END):
        # boost velocity in the direction of pointing.
        x=x+vx*click
        y=y+vy*click
        xpos=x+r*cos(theta)
        ypos=y+r*sin(theta)
        ax=a*cos(theta)
        ay=a*sin(theta)
        vx=vx+click*ax
        vy=vy+click*ay
        theta=theta+omega*click

        if (len(windowX)>8):
            windowX.pop(0)
        if (len(windowY)>8):
            windowY.pop(0)
        windowX.append(xpos)
        windowY.append(ypos)

        # put out a line if  the right time has passed.
        
        if ((t-lastT)>REPORT_INCREMENT):
            sys.stdout.write(".")
            lastT=t
            out.write("%.6f\t" % t)
            out.write("%.6f\t" % theta)
            out.write("%.6f\t" % xpos)
            out.write("%.6f\t" % ypos)
            # relative acceleration is a 2-tuple
            accelRel=d2(windowX,windowY,click,theta)
            out.write("%.6f\t%.6f\t" % (-accelRel[0],-accelRel[1]))
            out.write("%.6f\t" % sqrt(accelRel[0]**2+accelRel[1]**2))
            out.write("%.6f\n" % esterr(windowX,windowY,click))
        t+=click
    sys.stdout.write("\nDONE.\n")

def doMain(args):
    # make output directory
    try:
        os.stat("output")
    except:
        os.mkdir("output")
    for source in args:
        # for each variable file given, read variables, and run the simualtion with those variables.
        vars=loadVariables(source)
        runSim(vars,"output/%s" % source)

if __name__== "__main__":
    if (len(sys.argv)<2):
        sys.stderr.write("usage: %s {space delimited list of files containing var=value for initial variables}\n")
        sys.exit(2)
    doMain(sys.argv[1:])
