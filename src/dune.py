from ocp_vscode import show
from build123d import *
from math import *
from gears import *
from motors import *
from pathlib import Path

def b830():
    return Box(165/2, 55, 8.5)

def customize(obj, name, col):
    obj.name = name
    obj.color = Color(col)

def rotated(x, y, angle):
    cs = cos(angle)
    sn = sin(angle)
    X =  cs*x + sn*y
    Y = -sn*x + cs*y
    return (X, Y)

def trapezoid(length, th, width):
    a = 60
    t = Plane.YZ*Trapezoid(width, th, a, a)
    t = Pos(-length/2, 0, th/2)*extrude(t, length)
    return t

def makeSmallGear(th, r1, r2):
    g = SpurGear(
        module=2,
        tooth_count=12,
        pressure_angle=14.5,
        root_fillet=0.5,
        thickness=th,
    )
    g = Pos(0,0,th/2)*g
    g += Pos(0,0,-15)*Cylinder(r2, 30),
    g = Rot(0,0,360/12/2) * g
    return g

def makeLargeGear(r, th, holeR, spikeH):
    s = 10
    largeGear = SpurGear(
        module=2,
        tooth_count=48,
        pressure_angle=14.5,
        root_fillet=0.5,
        thickness=th,
    )
    largeGear = Pos(0,0,th/2)*largeGear
    largeGear -= Cylinder(r-s, th*4)
    largeGear += Pos(0,0,th/2)*Box(r*2-s, s, th)
    largeGear += Pos(0,0,th/2)*Box(s, r*2-s, th)
    largeGear += Pos(0,0,th/2)*Cylinder(15, th)
    largeGear -= Cylinder(holeR, th*4)
    largeGear += Pos(42.5,5,spikeH/2+th)*Box(5,5,spikeH)
    largeGear += Pos(-42.5,5,spikeH/2+th)*Box(5,5,spikeH)
    largeGear += Pos(42.5,-5,spikeH/2+th)*Box(5,5,spikeH)
    largeGear += Pos(-42.5,-5,spikeH/2+th)*Box(5,5,spikeH)
    return largeGear

def makeSlot(width, th, sideWidth, holeR):
    length = 130
    slot = Box(length-width, width, th)
    slot += Pos(length/2-width/2)*Cylinder(width/2, th)
    slot += Pos(width/2-length/2)*Cylinder(width/2, th)
    slot = Pos(0, 0, th/2) * slot
    slot -= Pos(0, 0, th/2) * trapezoid(length, th, width-sideWidth)
    slot -= Cylinder(holeR, th*4)
    return slot

def makeRack(width, th, sideWidth, gap):
    length = 176
    r = width/2-(5+gap)/2
    hole = width-20
    dr = 1/tan(60/180*pi)*th
    rack = trapezoid(length, th, width-sideWidth-gap)
    rack += Pos(length/2,0,th/2)*Cone(r, r-dr, th)
    rack += Pos(-length/2,0,th/2)*Cone(r, r-dr, th)
    rack -= Box(length, hole, 30)
    rack -= Pos(length/2)*Cylinder(hole/2, 30)
    rack -= Pos(-length/2)*Cylinder(hole/2, 30)

    # 2. ГЕНЕРИРУЕМ ПРАВИЛЬНЫЙ ЗУБ РЕЙКИ
    pitch = 2 * pi  # Шаг зубьев для модуля 2 (~6.283 мм)
    tooth_height = 2.25 * 2  # Полная высота зуба (4.5 мм)
    angle_rad = radians(18)  # Угол давления 30 градусов

    # Расчет ширины вершины и основания зуба рейки
    top_width = (pitch / 2) - 2 * (tooth_height / 2) * tan(angle_rad)
    bottom_width = (pitch / 2) + 2 * (tooth_height / 2) * tan(angle_rad)

    with BuildSketch() as tooth_sketch:
        # Рисуем симметричную трапецию зуба
        Polygon([
            (-bottom_width / 2, 0),
            (-top_width / 2, tooth_height),
            (top_width / 2, tooth_height),
            (bottom_width / 2, 0)
        ])

    # Выдавливаем и поворачиваем
    rackTooth = extrude(tooth_sketch.sketch, -th)
    rackTooth =  rackTooth

    # 3. РАССТАВЛЯЕМ ЗУБЬЯ ПО РЕЙКЕ
    # Обратите внимание: шаг перемещения (i) должен быть равен pitch (~6.283), а не 6!
    for i in range(29):  # 28 зубьев примерно заполнят длину 180 мм
        # Смещение по X идет строго кратно шагу pitch
        x_pos = (i - 14) * pitch
        rack += Pos(x_pos, -width / 2 +10, th) * rackTooth

    return rack


def makeMagnetHolder():
    h = Sphere(25)
    h -= Pos(0,0,-12)*Box(60,60,60)
    h -= Pos(0,0,25)*Cylinder(6,5)
    for i in range(6):
        a = pi/2+i/5*pi
        x = cos(a)*15
        y = sin(a)*15
        h += Pos(x,y,17)*Cylinder(1,3)
    h = Pos(0,0,-3)*h
    return h

def makeStand(size, height, g1Shift):
    thickness = 7
    sz = 20
    
    stand = extrude(Plane.YZ*RectangleRounded(size, height*2, 20),sz)
    stand -= Pos(0,0,-250)*Box(500,500,500)
    stand -= extrude(Plane.YZ*RectangleRounded(size-thickness*2, height*2-thickness*2, 14),sz)
    stand = Pos(-sz/2,0,-height/2)*stand
    stand = stand + Rot(0,0,90) * stand
    stand = Pos(0,0,-height/2)*stand
    stand += Pos(0,0,-thickness-5)*Cone(15,10, 10)
    stand += Pos(0,g1Shift,-thickness-5)*Cone(15,10, 10)
    stand -= Cylinder(holeR, 100)
    stand -= Pos(0,g1Shift)*Cylinder(holeR, 100)

    return stand

def makeBg(mainSize, g1Shift):
    dr = 1
    th = 5
    sz=8
    bg = Rot(0,0,360/16)*extrude(Circle(mainSize/2+dr),-th)
    bg -= Rot(0,0,360/16)*extrude(Circle(mainSize/2+dr-sz),-th)
    motorHolder = extrude(RectangleRounded(48,48,8),3)
    bg += motorHolder
    bg += Pos(0,g1Shift)*motorHolder
    dx = 22
    bg += Pos(0,dx)*extrude(Rectangle(mainSize-sz, sz),-th)
    bg += Pos(0,-dx)*extrude(Rectangle(mainSize-sz, sz),-th)
    bg += Pos(dx)*extrude(Rectangle(sz,mainSize-sz),-th)
    bg += Pos(-dx)*extrude(Rectangle(sz,mainSize-sz),-th)
    
    for i in range(8):
        r = mainSize/2-sz/2+dr/2
        a = i/4*pi+pi/8
        x = cos(a)*r
        y = sin(a)*r
        bg -= Pos(x,y)*Cylinder(1.5, th*2)
    return bg


mainSize = 185
largeGearR = 50
smallGearR = 10.5
gearsGap = 1.2
gearTh = 5
slotTh = 8
rackTh = 6
holeR = 5
width = 49
sideWidth = 5
gap = 0.1
motorHeight = 39

g1Shift = 60

largeGear = makeLargeGear(largeGearR, gearTh, holeR, slotTh/2,)
customize(largeGear, "largeGear", "#b0e792")

slot = Pos(0,0,gearTh)*makeSlot(width, slotTh, sideWidth, holeR) - largeGear
customize(slot, "slot", "#e7a692")

magnetHolder = makeMagnetHolder()
customize(magnetHolder, "magnetHolder", "#709f9e")

rack = Pos(176/2,0,slotTh/2+gearTh)*makeRack(width, rackTh, sideWidth, gap)
#rack -= magnetHolder
customize(rack, "rack", "#92e7e6")

centralMotor = Pos(0,0,gearTh-motorHeight)*nema17()
customize(centralMotor, "centralMotor", "#57a642")

sideMotor = Pos(0,g1Shift,gearTh-motorHeight)*nema17()
customize(sideMotor, "sideMotor", "#73bd70")

sideGear = makeSmallGear(gearTh, smallGearR, holeR-gap)
sideGear = Pos(0,g1Shift)*sideGear
sideGear -= sideMotor
customize(sideGear, "sideGear", "#f4f490")

centralGear = makeSmallGear(gearTh, smallGearR, holeR-gap)
centralGear = Pos(0,0,gearTh+slotTh/2)*centralGear
centralGear -= centralMotor
customize(centralGear, "centralGear", "#a4a490")

stand = makeStand(mainSize, motorHeight-gearTh, g1Shift)
stand -= sideMotor + centralMotor
customize(stand, "stand", "#cccccc")

bg = makeBg(mainSize, g1Shift)
bg = Pos(0,0,-motorHeight+gearTh)*bg
bg -= centralMotor
bg -= sideMotor
bg -= stand
customize(bg, "bg", "#eeeeee")

bb = Pos(55,0,-30)*Rot(0,0,90)*b830()


show(bb, bg, stand, sideGear, largeGear, 
    slot, rack, magnetHolder, centralGear,  
    sideMotor, centralMotor)



dir_path = Path("./models")
dir_path.mkdir(parents=True, exist_ok=True)

export_step(slot, "./models/slot.step")
export_step(rack, "./models/rack.step")
export_step(centralGear, "./models/centralGear.step")
export_step(largeGear, "./models/largeGear.step")