"""Custom pathfinding algorithm."""

from __future__ import annotations

from modules import position
from modules import settings
from modules import world
from modules import calc

from dataclasses import dataclass
import math


class PF_MoveType:
    WALK = 0
    JUMP_WALK = 1
    FALL_WALK = 2


@dataclass
class PF_Node:
    """
    PathFinding node represents position that player can be moved to.
    It contains information about it's parent PF_Node (or None for master node)
    After checking this node it will possibly gain children - other PF_Node(s).
    
    The movetype and direction parameters are information how to move to this
      specific node from it's parent. (ex. WALK at 90 degrees)
    """

    parent: PF_Node | None
    pos: position.Coordinate
    direction: position.AngleDirection | None
    movetype: PF_MoveType | None
    children: list[PF_Node]

    def get_cost(self) -> int:
        """Calculate node's trace cost (length)."""
        cost = 1
        if self.parent is not None:
            cost += self.parent.get_cost()
        return cost

    def has_node(self, node: PF_Node) -> bool:
        """Checks if provided node is one of this node's children node."""
        if node in self.children:
            return True

        for child in self.children:
            if child.has_node(node):
                return True
        return False

    def as_move(self) -> tuple[position.AngleDirection, PF_MoveType]:
        """Converts this object into move data."""
        return (self.direction, self.movetype)

    def to_moves_sequence(self) -> list[tuple[position.AngleDirection, PF_MoveType]]:
        """
        Converts this node and all it's parents into sequence of move data.
        Sequence starts from master node (start position) and ends on the last node.
        """
        moves = []
        current_node = self
        while current_node.parent is not None:
            moves.append(current_node.as_move())
            current_node = current_node.parent

        return moves[::-1]


class PathFinder:
    def __init__(
        self, start: position.Coordinate, dest: position.Coordinate, world: world.World
    ):
        self.start = start
        self.dest = dest
        self.world = world

        self.nodes: list[PF_Node] = []
        self.dest_nodes: list[PF_Node] = []
        self.backup_node: PF_Node | None = None
        self.backup_dist: int = 100

        self.__checked: dict[position.Coordinate : PF_Node] = {}

    def __new_node(
        self,
        parent: PF_Node | None,
        pos: position.Coordinate,
        direction: position.AngleDirection | None = None,
        movetype: PF_MoveType | None = None,
    ) -> PF_Node:
        """
        Creates new node or uses cached one.
        Automatically saves it as a closest node if it is one.
        """
        existing_node = self.__checked.get(pos)
        if existing_node is not None:
            return existing_node

        node = PF_Node(parent, pos, direction, movetype, [])
        self.__checked[pos] = node
        self.nodes.append(node)

        goal_dist = math.dist(pos.as_tuple(), self.dest.as_tuple())
        if goal_dist < self.backup_dist:
            self.backup_dist = goal_dist
            self.backup_node = node

        return node

    def __get_cheapest_node(self, nodes_seq: list[PF_Node]) -> PF_Node | None:
        """Get the cheapest node from an sequence of nodes."""
        if not nodes_seq:
            return None

        cheapest = nodes_seq[0]
        cost = cheapest.get_cost()
        for node in nodes_seq:
            new_cost = node.get_cost()
            if new_cost < cost:
                cost = new_cost
                cheapest = node

        return node

    def find(self) -> PF_Node | None:
        """
        Finds destination/close path and returns it's PF_Node.
        
        - destination: Leads exactly to requested point.
        - close: The nearest possible position player can go to.
        """
        master_node = self.__new_node(None, self.start)
        for node in self.nodes:
            self.check_node(node)

        dest_node = self.__get_cheapest_node(self.dest_nodes)
        close_node = self.backup_node

        if dest_node is not None:
            return dest_node

        if dest_node is None:
            if close_node is None and self.backup_node is None:
                print("No path found...")
                return None

            if close_node is not None:
                print("No direct path found, using closest...")
                return close_node

    def check_node(self, node: PF_Node) -> None:
        """Finds and saves all next possible moves from this node."""

        for direction, next_pos in calc.get_cross_bounding_pos(node.pos).items():
            # Define all reachable positions and ways to acheive them.
            actually_reachable = []

            # Check all next possibilites. Filter unreachable.
            for possibly_reachable_pos in self.world.reachable_grounds_at(
                next_pos.x, next_pos.y
            ):

                # Out of chunk position?
                if (
                    possibly_reachable_pos.x < 0
                    or possibly_reachable_pos.y < 0
                    or possibly_reachable_pos.x > settings.CHUNK_SIZE
                    or possibly_reachable_pos.y > settings.CHUNK_SIZE
                ):
                    continue

                # Same Z, no colliding voxels on the way.
                if possibly_reachable_pos.z == node.pos.z:
                    reachable_node = self.__new_node(
                        node, possibly_reachable_pos, direction, PF_MoveType.WALK
                    )
                    actually_reachable.append(reachable_node)

                # Lower Z, requires falling.
                if possibly_reachable_pos.z < node.pos.z:

                    # Is there colliding voxel disabling move possibility?
                    if not self.world.get_at_coord(next_pos.add_z(1)):

                        # Is this the first voxel i will hit when falling?
                        new_z = self.world.nearest_lower_ground_at(
                            next_pos.x, next_pos.y, next_pos.z
                        )
                        new_pos = position.Coordinate(next_pos.x, next_pos.y, new_z)
                        if new_pos == possibly_reachable_pos:

                            reachable_node = self.__new_node(
                                node, new_pos, direction, PF_MoveType.FALL_WALK
                            )
                            actually_reachable.append(reachable_node)

                # Higher Z.
                if possibly_reachable_pos.z > node.pos.z:

                    # Is this block reachable from current height.
                    if possibly_reachable_pos.z <= node.pos.z + 3:
                        # Three blocks jump.
                        if possibly_reachable_pos.z == node.pos.z + 3:
                            # Is there voxel on the way?
                            if (
                                self.world.get_at_coord(node.pos.add_z(3)) is None
                                and self.world.get_at_coord(node.pos.add_z(4)) is None
                                and self.world.get_at_coord(node.pos.add_z(5)) is None
                            ):

                                reachable_node = self.__new_node(
                                    node,
                                    possibly_reachable_pos,
                                    direction,
                                    PF_MoveType.JUMP_WALK,
                                )
                                actually_reachable.append(reachable_node)

                        # Two blocks jump.
                        if possibly_reachable_pos.z == node.pos.z + 2:
                            # Is there voxel on the way?
                            if (
                                self.world.get_at_coord(node.pos.add_z(3)) is None
                                and self.world.get_at_coord(node.pos.add_z(4)) is None
                            ):

                                reachable_node = self.__new_node(
                                    node,
                                    possibly_reachable_pos,
                                    direction,
                                    PF_MoveType.JUMP_WALK,
                                )
                                actually_reachable.append(reachable_node)

                        # One block elevation.
                        if possibly_reachable_pos.z == node.pos.z + 1:
                            # Is there voxel on the way?
                            if self.world.get_at_coord(node.pos.add_z(3)) is None:
                                reachable_node = self.__new_node(
                                    node,
                                    possibly_reachable_pos,
                                    direction,
                                    PF_MoveType.WALK,
                                )
                                actually_reachable.append(reachable_node)

            # Dead end.
            if not actually_reachable:
                continue

            for reachable_node in actually_reachable:

                # Save reachable nodes.
                node.children.append(reachable_node)

                if reachable_node.pos == self.dest:
                    self.dest_nodes.append(reachable_node)
