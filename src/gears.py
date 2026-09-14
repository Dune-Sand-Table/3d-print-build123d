from build123d import *
from math import *
from typing import Optional, Union

class InvoluteToothProfile(BaseLineObject):
    _applies_to = [BuildLine._tag]
    def __init__(
        self,
        module: float,
        tooth_count: int,
        pressure_angle: float,
        root_fillet: Optional[float] = None,
        addendum: Optional[float] = None,
        dedendum: Optional[float] = None,
        closed: bool = False,
        mode: Mode = Mode.ADD,
    ):
        self.module = module
        self.tooth_count = tooth_count
        self.pitch_radius = module * tooth_count / 2
        self.base_radius = self.pitch_radius * cos(radians(pressure_angle))
        self.addendum = addendum if addendum is not None else module
        self.addendum_radius = self.pitch_radius + self.addendum
        self.dedendum = dedendum if dedendum is not None else 1.25 * module
        self.root_radius = self.pitch_radius - self.dedendum
        half_thick_angle = 90 / tooth_count
        half_pitch_angle = half_thick_angle + degrees(
            tan(radians(pressure_angle)) - radians(pressure_angle)
        )
        # # Create the involute curve points
        involute_size = self.addendum_radius - self.base_radius
        pnts = []
        for i in range(11):
            r = self.base_radius + involute_size * i / 10
            α = acos(self.base_radius / r)  # in radians
            involute = tan(α) - α
            if (rp := r * cos(involute)) > self.root_radius:
                pnts.append((rp, r * sin(involute)))

        with BuildLine() as tooth:
            rotated_pnts = [
                Vector(*point).rotate(Axis.Z, -half_pitch_angle)
                for point in pnts
            ]
            l1 = Spline(*rotated_pnts)
            root_flank = Vector(self.root_radius, 0).rotate(
                Axis.Z, -half_pitch_angle
            )
            l2 = Line(rotated_pnts[0], root_flank)
            root = RadiusArc(
                l2 @ 1,
                Vector(self.root_radius, 0).rotate(Axis.Z, -2 * half_thick_angle),
                self.root_radius,
            )
            top_land = RadiusArc(
                l1 @ 1,
                Vector(self.addendum_radius, 0),
                -self.addendum_radius,
            )
            if root_fillet is not None:
                try:
                    fillet(tooth.vertices().sort_by(Axis.X)[1], root_fillet)
                except StdFail_NotDone as err:
                    raise ValueError(
                        "Invalid root radius, try a smaller value"
                    ) from err

            mirror(tooth.edges(), about=Plane.XZ)

        close = (
            [
                Edge.make_line(
                    tooth.line.vertices().sort_by(Axis.Y)[-1].to_tuple(),
                    tooth.line.vertices().sort_by(Axis.Y)[0].to_tuple(),
                )
            ]
            if closed
            else []
        )

        super().__init__(Wire.combine(tooth.line.edges() + close)[0], mode=mode)


class SpurGearPlan(BaseSketchObject):

    _applies_to = [BuildSketch._tag]

    def __init__(
        self,
        module: float,
        tooth_count: int,
        pressure_angle: float,
        root_fillet: Optional[float] = None,
        addendum: Optional[float] = None,
        dedendum: Optional[float] = None,
        rotation: float = 0,
        align: Union[Align, tuple[Align, Align]] = (Align.CENTER, Align.CENTER),
        mode: Mode = Mode.ADD,
    ):
        gear_tooth = InvoluteToothProfile(
            module, tooth_count, pressure_angle, root_fillet, addendum, dedendum
        )
        self.pitch_radius = gear_tooth.pitch_radius
        self.base_radius = gear_tooth.base_radius
        self.addendum_radius = gear_tooth.addendum_radius
        self.root_radius = gear_tooth.root_radius
        if self.base_radius < self.root_radius:
            raise ValueError("Invalid configuration, try changing the pressure angle")
        gear_teeth = PolarLocations(0, tooth_count) * gear_tooth
        gear_wire = Wire([e for tooth in gear_teeth for e in tooth.edges()])
        gear_face = Face(gear_wire)
        if gear_face.normal_at().Z < 0:
            gear_face = -gear_face
        super().__init__(gear_face, rotation, align, mode)


class SpurGear(BasePartObject):


    _applies_to = [BuildPart._tag]

    def __init__(
        self,
        module: float,
        tooth_count: int,
        pressure_angle: float,
        thickness: float,
        root_fillet: Optional[float] = None,
        addendum: Optional[float] = None,
        dedendum: Optional[float] = None,
        rotation: RotationLike = (0, 0, 0),
        align: Union[None, Align, tuple[Align, Align, Align]] = Align.CENTER,
        mode: Mode = Mode.ADD,
    ):
        gear_plan = SpurGearPlan(
            module, tooth_count, pressure_angle, root_fillet, addendum, dedendum
        )
        self.pitch_radius = gear_plan.pitch_radius
        self.base_radius = gear_plan.base_radius
        self.addendum_radius = gear_plan.addendum_radius
        self.root_radius = gear_plan.root_radius
        super().__init__(
            extrude(gear_plan, amount=thickness),
            rotation,
            align,
            mode,
        )
        