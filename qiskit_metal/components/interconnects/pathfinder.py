import numpy as np
from numpy.linalg import norm
import heapq

# The A* algorithm can find the shortest path between 2 given anchors.
# Input the coordinates of these anchors as start and end.

class State:

    # TODO: Use Manhattan distance instead of Euclidean norm since we're using snap by default?
    # TODO: If 2 consecutive line segments point in the same direction, concatenate them into 1
    # TODO: Find a good way of determining step size (fast runtime + no overshooting)
    
    def __init__(self, coord, origin, start=np.array([0, 0]), end=np.array([0, 0]), step_size=1):
        self.neighbors = []
        self.step_size = step_size
        self.origin = origin # the last State object created prior to coord
        self.coord = coord # 2D numpy array of the form np.array([xi, yi])
        self.dist = norm(coord - end) # distance from current point to destination
        if origin:
            # coord is not the first point on this path
            self.path = origin.path + [coord]
            self.start = origin.start
            self.goal = origin.end
        else:
            # coord is the first point on this path
            self.path = [coord]
            self.start = start
            self.goal = end

    def get_neighbors(self):
        # Look in forward, left, and right directions a distance d away.
        # If there's no obstacle between the current point and this next step
        # as determined by the pairs of points in qgeometry, add it to the
        # list of neighbors.
        if self.origin:
            # Use last 2 points in path to determine where it points
            direction = self.path[-1] - self.path[-2]
            for disp in [np.array([0, 1]), np.array([0, -1]), np.array([1, 0]), np.array([-1, 0])]:
                # Unit displacement in 4 cardinal directions
                if np.dot(disp, direction) >= 0:
                    # Ignore backward direction
                    curpt = self.path[-1]
                    nextpt = curpt + self.step_size * disp
                    # Check to see whether line segment connecting these 2 points intersects any other
                    # pair of points that already exists in design.qgeometry
                    if not any(self.overlapping(curpt, nextpt, pt1, pt2) for pt1, pt2 in qgeometry):
                        self.neighbors.append(nextpt)

    def overlapping(self, a, b, c, d):
        # Returns whether segment ab intersects segment cd
        # TODO: Check for a way to order line segments in qgeometry for faster log(N)^2 searching
        pass

class AStarSolver:

    def __init__(self, start, end, step_size):
        self.path = []
        self.visited = set()
        self.h = [] # priority queue (heap in Python implementation)
        self.start = start
        self.end = end
        self.step_size = step_size # TODO: Find clever way of determining this

    def solve(self):
        startState = State(self.start, None, self.start, self.end, self.step_size)
        count = 0 # how many steps have been taken already along this path
        heapq.heappush(self.h, (norm(self.start - self.end), count, startState))
        # Elements in the heap are ordered by the following:
        # 1. How far they are from the destination (end)
        # 2. How many steps they've taken from the start (count -> see above)
        # 3. The state object itself (TODO: check if this can be sorted)
        while self.h and (not self.path):
            nearest_neighbor = heapq.heappop(self.h)[2]
            nearest_neighbor.get_neighbors()
            self.visited.add(nearest_neighbor.coord) # maybe can't hash np arrays -> tupleize
            for neighbor in nearest_neighbor.neighbors:
                if neighbor.coord not in self.visited:
                    count += 1
                    if not neighbor.dist:
                        self.path = neighbor.path
                        break
                    heapq.heappush(self.h, (neighbor.dist, count, ))