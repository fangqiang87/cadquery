from typing import Union, Optional, List, Dict, Callable, overload, Tuple, Iterable, Any
from typing_extensions import Literal
from math import tan, sin, cos, pi

from .occ_impl.shapes import Shape, Face, Edge, Wire, Compound
from .occ_impl.geom import Location, Vector

Modes = Literal["a", "s"]
Point = Union[Vector, Tuple[float, float]]


class Sketch(object):

    parent: Any

    faces: Compound
    wires: List[Wire]
    edges: List[Edge]

    selection: List[Union[Shape, Location]]

    tags: Dict[str, Shape]

    def __init__(self, parent: Any = None):

        self.parent = parent

        self.faces = Compound.makeCompound(())
        self.wires = []
        self.edges = []

        self.selection = []
        self.tags = {}

    # face construction
    def face(
        self,
        b: Union[Wire, Iterable[Edge]],
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        if isinstance(b, Wire):
            res = Face.makeFromWires(b)
        elif isinstance(b, Iterable):
            res = Face.makeFromWires(Wire.assembleEdges(b))
        else:
            raise ValueError(f"Unsupported argument {b}")

        res = res.rotate(Vector(), Vector(0, 0, 1), angle)

        return self.each(lambda l: res.located(l), mode, tag)

    def rect(
        self,
        w: float,
        h: float,
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        res = Face.makePlane(w, h).rotate(Vector(), Vector(0, 0, 1), angle)

        return self.each(lambda l: res.located(l), mode, tag)

    def circle(
        self, r: float, mode: Modes = "a", tag: Optional[str] = None
    ) -> "Sketch":

        res = Face.makeFromWires(Wire.makeCircle(r, Vector(), Vector(0, 0, 1)))

        return self.each(lambda l: res.located(l), mode, tag)

    def ellipse(
        self,
        a1: float,
        a2: float,
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        res = Face.makeFromWires(
            Wire.makeEllipse(
                a1, a2, Vector(), Vector(0, 0, 1), Vector(1, 0, 0), rotation_angle=angle
            )
        )

        return self.each(lambda l: res.located(l), mode, tag)

    def trapezoid(
        self,
        w: float,
        h: float,
        a1: float,
        a2: Optional[float] = None,
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        v1 = Vector(-w / 2, -h / 2)
        v2 = Vector(w / 2, -h / 2)
        v3 = Vector(-w / 2 + h / tan(a1), h / 2)
        v4 = Vector(w / 2 - h / tan(a2 if a2 else a1), h / 2)

        return self.polygon((v1, v2, v3, v4), angle, mode, tag)

    def slot(
        self,
        w: float,
        h: float,
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        p1 = Vector(-w / 2, h / 2)
        p2 = Vector(w / 2, h / 2)
        p3 = Vector(-w / 2, -h / 2)
        p4 = Vector(w / 2, -h / 2)
        p5 = Vector(-w / 2 - h / 2, 0)
        p6 = Vector(w / 2 + h / 2, 0)

        e1 = Edge.makeLine(p1, p2)
        e2 = Edge.makeThreePointArc(p2, p6, p4)
        e3 = Edge.makeLine(p4, p3)
        e4 = Edge.makeThreePointArc(p3, p5, p1)

        w = Wire.assembleEdges((e1, e2, e3, e4))

        return self.face(w, angle, mode, tag)

    def regularPolygon(
        self,
        r: float,
        n: int,
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        pts = [r * Vector(sin(i * 2 * pi / n), cos(i * 2 * pi / n)) for i in range(n)]

        return self.polygon(pts, angle, mode, tag)

    def polygon(
        self,
        pts: Iterable[Point],
        angle: float = 0,
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        w = Wire.makePolygon(pts)

        return self.face(w, angle, mode, tag)

    # distribute locations

    def rarray(self, xs: float, ys: float, nx: int, ny: int) -> "Sketch":
        ...

    def parray(
        self, r: float, a1: float, a2: float, n: int, rotate: bool = True
    ) -> "Sketch":
        ...

    def distribute(self, n: int, rotate: bool = True) -> "Sketch":
        ...

    def push(self, locs: Iterable[Location]) -> "Sketch":
        ...

    def each(
        self,
        callback: Callable[[Location], Union[Face, "Sketch"]],
        mode: Modes = "a",
        tag: Optional[str] = None,
    ) -> "Sketch":

        res: Union[Face, "Sketch"] = []

        if self.selection:
            for el in self.selection:
                if isinstance(el, Location):
                    loc = el
                elif isinstance(el, Shape):
                    loc = Location(el.Center())
                else:
                    raise ValueError(f"Invalid selection: {el}")

                res.append(callback(loc))
        else:
            res.append(callback(Location()))

        if tag:
            self.tags[tag] = res

        if mode == "a":
            self.faces = self.faces.fuse(*res)
        elif mode == "s":
            self.faces = self.faces.cut(*res)
        else:
            raise ValueError(f"Invalid mode: {mode}")

        return self

    # modifiers

    def offset(
        self, d: float, mode: Modes = "a", tag: Optional[str] = None
    ) -> "Sketch":
        ...

    def fillet(self, d: float) -> "Sketch":
        ...

    def chamfer(self, d: float) -> "Sketch":
        ...

    # selection

    def faces(self, s: str) -> "Sketch":
        ...

    def wires(self, s: str) -> "Sketch":
        ...

    def edges(self, s: str) -> "Sketch":
        ...

    def vertices(self, s: str) -> "Sketch":
        ...

    def reset(self) -> "Sketch":

        self.selection = []
        return self

    def delete(self) -> "Sketch":

        for obj in self.selection:
            if isinstance(obj, Face):
                self.faces.remove(obj)
            elif isinstance(obj, Wire):
                self.wires.remove(obj)
            else:
                self.edges.remove(obj)

        self.selection = []

        return self

    # edge based interface

    @overload
    def segment(self, p1: Point, p2: Point, tag: Optional[str] = None) -> "Sketch":
        ...

    @overload
    def segment(self, p2: Point, tag: Optional[str] = None) -> "Sketch":
        ...

    @overload
    def segment(self, l: float, a: float, tag: Optional[str] = None) -> "Sketch":
        ...

    @overload
    def arc(
        self, p1: Point, p2: Point, r: float, tag: Optional[str] = None
    ) -> "Sketch":
        ...

    @overload
    def arc(self, p2: Point, a: float, tag: Optional[str] = None) -> "Sketch":
        ...

    @overload
    def arc(
        self, c: Point, r: float, a1: float, a2: float, tag: Optional[str] = None
    ) -> "Sketch":
        ...

    def spline(self, pts: Iterable[Point], tag: Optional[str] = None) -> "Sketch":
        ...

    def close(self, tag: Optional[str] = None) -> "Sketch":
        ...

    def assemble(self, mode: Modes = "a", tag: Optional[str] = None) -> "Sketch":
        ...

    # misc

    def finalize(self) -> Any:

        return self.parent
