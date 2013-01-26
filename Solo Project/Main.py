import direct.directbase.DirectStart #starts Panda
from pandac.PandaModules import * #basic Panda modules
from direct.showbase.DirectObject import DirectObject #for event handling
from direct.actor.Actor import Actor #for animated models
from direct.interval.IntervalGlobal import * #for compound intervals
from direct.task import Task #for update functions
import math, sys, os, random

class World(DirectObject): #necessary to accept events
    def __init__(self):
        
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)
        
        #turn off default mouse control
        #otherwise we can't position the camera
        base.disableMouse()
        #camera.setPosHpr(0, -15, 7, 0, -15, 0)
        
        self.keyMap = {"left":0, "right":0, "forward":0, "cam-left":0, "cam-right":0}
        self.prevTime = 0
        taskMgr.add(self.move, "moveTask")
        self.loadModels()
        self.setupLights()
        self.setupCollisions()
        #self.pandaWalk = self.panda.posInterval(1, (0, -5, 0))
        self.accept("escape", sys.exit) #message name, function to call, (optional) list of arguments to that function
        #self.accept("arrow_up", self.walk)
        #other useful interval methods:
        # loop, pause, resume, finish
        # start can optionally take arguments: starttime, endtime, playrate
        
        #for fixed interval movement
        #self.accept("arrow_left", self.turn, [-1]) #yes, you have to use a list, event if the function only takes one argument
        #self.accept("arrow_right", self.turn, [1])
        
        #set up chase cam
        camera.setPos(self.vtol.getX(), self.vtol.getY()+10, 2)
        
        #for "continuous" control
        self.accept("a", self.setKey, ["cam-left",1])
        self.accept("s", self.setKey, ["cam-right",1])
        self.accept("a-up", self.setKey, ["cam-left",0])
        self.accept("s-up", self.setKey, ["cam-right",0])
        
        self.accept("arrow_up", self.setKey, ["forward", 1])
        self.accept("arrow_left", self.setKey, ["left", 1])
        self.accept("arrow_right", self.setKey, ["right", 1])
        self.accept("arrow_up-up", self.setKey, ["forward", 0])
        self.accept("arrow_left-up", self.setKey, ["left", 0])
        self.accept("arrow_right-up", self.setKey, ["right", 0])

    def setKey(self, key, value):
        self.keyMap[key] = value
        
    def loadModels(self):
        """loads initial models into the world"""
        
        # Get the location of the 'py' file I'm running:
        mydir = os.path.abspath(sys.path[0])
        
        # Convert that to panda's unix-style notation.
        mydir = Filename.fromOsSpecific(mydir).getFullpath()
        
        self.env = loader.loadModel(mydir + "/models/floor.egg")
        self.env.reparentTo(render)
        self.env.setScale(7)
        self.env.setPos(0, 0, -11)
        
        self.vtol = loader.loadModel(mydir + "/models/vtol thing.egg")
        self.vtol.reparentTo(render)
        self.vtol.setScale(.1)
        self.vtol.setH(180)
        
        self.building1s = []
        for i in range(2):
            building1 = loader.loadModel(mydir + "/models/Building.egg")
            building1.setScale(1)
            building1.setPos(30*i, 30*i + 30, -10)
            building1.reparentTo(render)
            self.building1s.append(building1)
        
        self.building2s = []
        for j in range(2):
            building2 = loader.loadModel(mydir + "/models/Building2.egg")
            building2.setScale(1)
            building2.setPos(20*j, 30*j, -10)
            building2.reparentTo(render)
            self.building2s.append(building2)
        
            
        
    def setupLights(self):
        """loads initial lighting"""
        self.ambientLight = AmbientLight("ambientLight")
        #for setting colors, alpha is largely irrelevant
        self.ambientLight.setColor((.25, .25, .25, 1.0))
        #create a NodePath, and attach it directly into the scene
        self.ambientLightNP = render.attachNewNode(self.ambientLight)
        #the node that calls setLight is what's illuminated by the given light
        #you can use clearLight() to turn it off
        render.setLight(self.ambientLightNP)
        '''
        self.dirLight = DirectionalLight("dirLight")
        self.dirLight.setColor((.6, .6, .6, 1))
        self.dirLightNP = render.attachNewNode(self.dirLight)
        self.dirLightNP.setHpr(0, -25, 0)
        render.setLight(self.dirLightNP)
        '''
        self.headLightR = Spotlight("headLightR")
        self.headLightR.setColor((1, 1, 1, 1))
        lens = PerspectiveLens()
        self.headLightRNP = self.vtol.attachNewNode(self.headLightR)
        self.headLightRNP.setPos(self.vtol.getX() + 1, self.vtol.getY(), 0)
        self.headLightRNP.setHpr(0,-180,0)
        render.setLight(self.headLightRNP)
        
    # def walk(self):
    #     dist = 5
    #     dx = dist * math.sin(deg2Rad(self.panda.getH()))
    #     dy = dist * -math.cos(deg2Rad(self.panda.getH()))
    #     pandaWalk = self.panda.posInterval(1, (self.panda.getX() + dx, self.panda.getY() + dy, 0))
    #     pandaWalk.start()
    #     
    # def turn(self, direction):
    #     """turn the panda"""
    #     pandaTurn = self.panda.hprInterval(.2, (self.panda.getH() - (10*direction), 0 ,0))
    #     pandaTurn.start()
    
    def move(self, task):
        """compound interval for walking"""
        dt = task.time - self.prevTime
        #stuff and things
        camera.lookAt(self.vtol)
        if (self.keyMap["cam-left"] != 0):
            base.camera.setX(base.camera, -20 * globalClock.getDt())
        if (self.keyMap["cam-right"] != 0):
            base.camera.setX(base.camera, +20 * globalClock.getDt())
        
        # if the camera is too close, move it father
        # if the camera is too far, move it closer
        camvec = self.vtol.getPos() - base.camera.getPos()
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()
        if (camdist > 15.0):
            base.camera.setPos(base.camera.getPos() + camvec*(camdist-15))
            camdist = 15.0
        if (camdist < 15.0):
            base.camera.setPos(base.camera.getPos() - camvec*(10-camdist))
            camdist = 10.0
        
        if (self.keyMap["left"] == 1):
            self.vtol.setH(self.vtol.getH() + 300 * globalClock.getDt())
            #self.vtol.setH(self.vtol.getH() + dt*100)
        if (self.keyMap["right"] == 1):
            self.vtol.setH(self.vtol.getH() - 300 * globalClock.getDt())
            #self.vtol.setH(self.vtol.getH() - dt*100)
        if self.keyMap["forward"] == 1:
            dist = .1
            angle = deg2Rad(self.vtol.getH())
            dx = dist * math.sin(angle)
            dy = dist * -math.cos(angle)
            self.vtol.setPos(self.vtol.getX() + dx, self.vtol.getY() + dy, 0)
            
        #fixes up the camera
        self.floater.setPos(self.vtol.getPos())
        self.floater.setZ(self.vtol.getZ() + 2.0)
        base.camera.lookAt(self.floater)

        self.prevTime = task.time
        return Task.cont
        
    def setupCollisions(self):
        #make a collision traverser, set it to default
        base.cTrav = CollisionTraverser()
        
        
        #self.cHandler = CollisionHandlerEvent()
        self.cHandler = CollisionHandlerPusher()
        
        #set the pattern for the event sent on collision
        # "%in" is substituted with the name of the into object
        #self.cHandler.setInPattern("hit-%in")
        
        cSphere = CollisionSphere((0,0,0), 10) #panda is scaled way down!
        cNode = CollisionNode("vtol")
        cNode.addSolid(cSphere)
        #panda is *only* a from object
        cNode.setIntoCollideMask(BitMask32.allOff())
        cNodePath = self.vtol.attachNewNode(cNode)
        #cNodePath.show()
        base.cTrav.addCollider(cNodePath, self.cHandler)
        self.cHandler.addCollider(cNodePath, self.vtol)
        
        for building1 in self.building1s:
            cTube1 = CollisionTube((-0.4,3,3), (-0.4,3,20), 6.8)
            cTube2 = CollisionTube((-0.4,-3,3), (-0.4,-3,20), 6.8)
            cNode = CollisionNode("models/Building")
            cNode.addSolid(cTube1)
            cNode.addSolid(cTube2)
            cNodePath = building1.attachNewNode(cNode)
            #cNodePath.show()
        
        for building2 in self.building2s:
            cTube3 = CollisionTube((3.5,7.5,3), (3.5,7.5,20), 6.8)
            cTube4 = CollisionTube((-4,-8,3), (-4,-8,20), 6.8)
            cNode = CollisionNode("models/Building2")
            cNode.addSolid(cTube3)
            cNode.addSolid(cTube4)
            cNodePath = building2.attachNewNode(cNode)
            #cNodePath.show()
        
        fromObject = base.camera.attachNewNode(CollisionNode('colNode'))
        fromObject.node().addSolid(CollisionSphere(0, 0, 0, 1))
        self.cHandler.addCollider(fromObject, base.camera, base.drive.node())
        
                
w = World()
run()