#!/usr/bin/python
import sys, copy,re
import numpy as np
import inkex, simpletransform,simplestyle,simplepath
import bezmisc
import cubicsuperpath
import numpy as np

def bernstein3():
    return np.array([[ 1., -3.,  3., -1.],
                     [-0.,  3., -6.,  3.],
                     [ 0., -0.,  3., -3.],
                     [-0.,  0., -0.,  1.]])

def bernsteinDerivative3():
    return np.array([[ -3.,   6.,  -3.],
                     [  3., -12.,   9.],
                     [ -0.,   6.,  -9.],
                     [  0.,  -0.,   3.]])

def index(subpath,a):
    n=3
    (x0,y0)=a
    summation=0j
    x=np.zeros((4,2))
    
    z0=x0+1j*y0
    
    for i in range(len(subpath)-1):
        [_,x[0],x[1]]=np.array(subpath[i])
        [x[2],x[3],_]=np.array(subpath[i+1])
        
        X=x[:,0]+1j*x[:,1]
        
        P=np.sum(bernsteinDerivative3()*X[:,None],axis=0)
        Q=np.sum(bernstein3()*(X[:,None]-z0),axis=0)       
        
        roots=np.roots(np.flip(Q,axis=0))
        if(len(roots)>0):
            A,B=np.meshgrid(roots,roots)
            C=A-B
            C[np.arange(n),np.arange(n)]=1
            a=np.prod(1/C,axis=-1)*np.polyval(np.flip(P,axis=0),roots)
            s=np.sum(a*np.log(1-1/roots))/Q[-1]
            summation+=s
        ind=(summation/2/np.pi/1j).real
    if(np.abs(ind-round(ind))>1e-6):
        inkex.debug("Path not closed")
    else:
        return int(round(ind))
        


#rootWrapper and linebezierintersect are redifnied from bezmisc.py
#because the original file uses an explicit formula for the roots that sometimes exhibits illicit behaviour
def rootWrapper(a,b,c,d):
    sol=np.roots([a,b,c,d])
    isreal=np.abs(np.imag(sol))<1e-9#is the threshold value correct ?
    return np.real(sol[isreal])

def linebezierintersect(((lx1,ly1),(lx2,ly2)),((bx0,by0),(bx1,by1),(bx2,by2),(bx3,by3))):
    #parametric line
    dd=lx1
    cc=lx2-lx1
    bb=ly1
    aa=ly2-ly1

    if aa:
        coef1=cc/aa
        coef2=1
    else:
        coef1=1
        coef2=aa/cc

    ax,ay,bx,by,cx,cy,x0,y0=bezmisc.bezierparameterize(((bx0,by0),(bx1,by1),(bx2,by2),(bx3,by3)))
    #cubic intersection coefficients
    a=coef1*ay-coef2*ax
    b=coef1*by-coef2*bx
    c=coef1*cy-coef2*cx
    d=coef1*(y0-bb)-coef2*(x0-dd)

    roots = rootWrapper(a,b,c,d)
    retval = []
    rett =[]
    for i in roots:
        if type(i) is complex and abs(i.imag)<1e-3:
            i = i.real
        if type(i) is not complex and 0<=i<=1:
            retval.append(bezmisc.bezierpointatt(((bx0,by0),(bx1,by1),(bx2,by2),(bx3,by3)),i))
            rett.append(i)
    return retval,rett

class RayTracing(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
    def effect(self):
        self.beamSeeds=[]
        self.optics=[]
        #examine each selected object to check if it's an optic and add it if it's the case
        #the optic description is done in the description field of the object
        for id,node in self.selected.iteritems():
            for child in node.getchildren():
               if(child.tag == inkex.addNS('desc','svg')): 
                    desc=child.text
                    pattern=re.search("optics:([a-z]*)(?::([0-9]+(.[0-9])?))?",desc)
                    if(pattern is not None):
                        type=pattern.group(1)
                        if(type=="beam"):
                            self.addBeam(node)
                        if(type=="beamdump"):
                            self.addBeamDump(node)
                        if(type=="mirror"):
                            self.addMirror(node)
                        if(type=="glass"):
                            self.addGlass(node,float(pattern.group(2)))
        #the borders of the document are defined as beam dumps to prevent the beam from going to infinity
        svg = self.document.getroot()
        width = self.unittouu(svg.get('width'))
        height = self.unittouu(svg.attrib['height'])
        A=[0,0]
        B=[width,0]
        C=[width,height]
        D=[0,height]
        self.optics.append({"bezier":[A,A,B,B],"type":"beamdump"})
        self.optics.append({"bezier":[B,B,C,C],"type":"beamdump"})
        self.optics.append({"bezier":[C,C,D,D],"type":"beamdump"})
        self.optics.append({"bezier":[D,D,A,A],"type":"beamdump"})
        
        for optic in self.optics:
            if(optic["type"]=="glass"):
                inkex.debug(optic["inside"])
        
        #cast every beam recursively 
        for beam in self.beamSeeds:
            path=self.cast(beam["origin"],beam["tangent"])
            string=""
            for [x,y] in path:
                string+=str(x)+","+str(y)+" "
            parent=beam["node"].getparent()
            line_attribs = {'style' : beam["node"].get("style"),
                        inkex.addNS('label','inkscape') : "test",
                        'd' : 'M '+ string}
            line = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )

    def cast(self,origin,tangent,depth=0):
        if(depth==sys.getrecursionlimit()-100):
            inkex.errormsg(_("Maximum recursion depth reached ({})".format(depth)))
            return [origin]
        x,optic=self.firstCollision(origin,tangent)
        if(optic["type"]=="beamdump"):
            return [origin,x]    
        if(optic["type"]=="mirror"):
            bezierTangent=bezmisc.bezierslopeatt(optic["bezier"],optic["t"])
            bezierTangent/=np.linalg.norm(bezierTangent)
            normal=np.array([bezierTangent[1],-bezierTangent[0]])
            if(np.dot(normal,tangent))>0:
                normal=-normal
            return [origin]+self.cast(x+1e-9*normal,tangent-2*normal*np.dot(tangent,normal),depth=depth+1)
        if(optic["type"]=="glass"):
            bezierTangent=bezmisc.bezierslopeatt(optic["bezier"],optic["t"])
            bezierTangent/=np.linalg.norm(bezierTangent)
            normal=np.array([bezierTangent[1],-bezierTangent[0]])
            if(np.dot(normal,tangent))>0:
                if(optic["inside"]=="left"):
                    n1=optic["opticalIndex"]
                    n2=1
                else:
                    n1=1
                    n2=optic["opticalIndex"]
                #the normal is on the same side as the incoming beam
                normal=-normal
            else:
                if(optic["inside"]=="right"):
                    n1=optic["opticalIndex"]
                    n2=1
                else:
                    n1=1
                    n2=optic["opticalIndex"]
            internalReflection=np.dot(tangent,normal)**2-(1-n2**2/n1**2)
            if(internalReflection>0):
                u2=n1/n2*(tangent+normal*(-np.dot(tangent,normal)-np.sqrt(internalReflection)))
                return [origin]+self.cast(x-1e-9*normal,u2,depth=depth+1)
            else:
                return [origin]+self.cast(x+1e-9*normal,tangent-2*normal*np.dot(tangent,normal),depth=depth+1)




            return [origin]+self.cast(x+1e-9*normal,tangent-2*normal*np.dot(tangent,normal),depth=depth+1)

        
    def firstCollision(self,origin,tangent):
        t=np.inf 
        opticHit={}
        opticHitCoordinate=0
        for optic in self.optics:
            #the solutions should be real but they have a 0j imaginary part that can be discarded 
            solutions,parameter=linebezierintersect((origin,origin+tangent),
                                optic["bezier"])
            for (hit,p) in zip(solutions,parameter):
                travelDistance=np.dot(hit-origin,tangent)
                if(travelDistance<t and travelDistance>0):
                    t=travelDistance
                    opticHit=optic
                    opticHit["t"]=p
        return origin+t*tangent,opticHit

                                    
    def addBeamDump(self,node):
        if(node.tag == inkex.addNS('path','svg')):
            pts=cubicsuperpath.parsePath(node.get("d"))
            for subpath in pts:
                for i in range(len(subpath)-1):
                    [_,x0,x1]=np.array(subpath[i])
                    [x2,x3,_]=np.array(subpath[i+1])
                    self.optics.append({"bezier":[x0,x1,x2,x3],"type":"beamdump"})
    def addGlass(self,node,opticalIndex):
        if(node.tag == inkex.addNS('path','svg')):
            pts=cubicsuperpath.parsePath(node.get("d"))
            for subpath in pts:
                [_,x0,x1]=np.array(subpath[0])
                [x2,x3,_]=np.array(subpath[1])
                dx,dy=bezmisc.bezierslopeatt((x0,x1,x2,x3),0.5)
                normal=np.array([dy,-dx])
                normal/=np.linalg.norm(normal)
                x,y=bezmisc.bezierpointatt((x0,x1,x2,x3),0.5)
                pointAtRight=np.array([x,y])+1e-6*normal
                if(index(subpath,pointAtRight)==0):
                    inside="left"
                else:
                    inside="right"
                
                for i in range(len(subpath)-1):
                    [_,x0,x1]=np.array(subpath[i])
                    [x2,x3,_]=np.array(subpath[i+1])
                    self.optics.append({"bezier":[x0,x1,x2,x3],"type":"glass","opticalIndex":opticalIndex,"inside":inside})

    def addMirror(self,node):
        if(node.tag == inkex.addNS('path','svg')):
            pts=cubicsuperpath.parsePath(node.get("d"))
            for subpath in pts:
                for i in range(len(subpath)-1):
                    [_,x0,x1]=np.array(subpath[i])
                    [x2,x3,_]=np.array(subpath[i+1])
                    self.optics.append({"bezier":[x0,x1,x2,x3],"type":"mirror"})

    def addBeam(self,node):
        if(node.tag == inkex.addNS('path','svg')):
            pts=cubicsuperpath.parsePath(node.get("d"))
            for subpath in pts:
                [_,x0,x1]=np.array(subpath[-2])
                [x2,x3,_]=np.array(subpath[-1])
                tangent=3*(x3-x2)
                #if the handles coincide with the nodes, the previous expression is 0 and not the true tangent
                #which is the second derivative at t=1
                if(np.linalg.norm(tangent)<1e-6):
                    tangent=(6*x1-12*x2+6*x3)*-1#I don't understand the -1
                self.beamSeeds.append({"origin":x3,"tangent":tangent/np.linalg.norm(tangent),"node":node})

        
effect = RayTracing()
effect.affect()
